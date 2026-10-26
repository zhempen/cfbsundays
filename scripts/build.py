#!/usr/bin/env python3
"""CFB Sundays data pipeline.

Downloads free nflverse data (rosters, weekly stats, snap counts, depth
charts, schedule) and writes the small JSON files the static site reads.
Run from the repo root: python3 scripts/build.py
"""
import csv, html, io, json, os, re, statistics, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from conferences import conference
from collections import defaultdict

# Current season. Change this each summer before week 1, then archive the
# season that just ended:  python3 scripts/build.py --archive 2026
SEASON = int(os.environ.get("SEASON", "2026"))
ROOT = os.path.join(os.path.dirname(__file__), "..", "site")
OUT = os.path.join(ROOT, "data")
ARCHIVE = os.path.join(ROOT, "archive")   # past seasons, committed (they don't change)
FIRST_ARCHIVE = 2013                      # snap counts (our starter test) begin in 2013

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
DRAFT_URL = f"{NFLVERSE}/draft_picks/draft_picks.csv"
PLAYERS_URL = f"{NFLVERSE}/players/players.csv"

def sources(season):
    return {
        "roster": f"{NFLVERSE}/rosters/roster_{season}.csv",
        "stats": f"{NFLVERSE}/stats_player/stats_player_week_{season}.csv",
        "snaps": f"{NFLVERSE}/snap_counts/snap_counts_{season}.csv",
        "depth": f"{NFLVERSE}/depth_charts/depth_charts_{season}.csv",
    }

# ---- game starters from ESPN (the official starting lineup for each game) ----
ESPN_TEAM = {"ARI": 22, "ATL": 1, "BAL": 33, "BUF": 2, "CAR": 29, "CHI": 3, "CIN": 4,
             "CLE": 5, "DAL": 6, "DEN": 7, "DET": 8, "GB": 9, "HOU": 34, "IND": 11,
             "JAX": 30, "KC": 12, "LV": 13, "OAK": 13, "LAC": 24, "SD": 24, "LA": 14,
             "STL": 14, "MIA": 15, "MIN": 16, "NE": 17, "NO": 18, "NYG": 19, "NYJ": 20,
             "PHI": 21, "PIT": 23, "SF": 25, "SEA": 26, "TB": 27, "TEN": 10, "WAS": 28}
ESPN_ROSTER = ("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{e}"
               "/competitions/{e}/competitors/{t}/roster")

def espn_starts(games_rows, cache):
    """{game_id: {team: [espn player ids who started]}} for finished games.
    Reuses cached games; a game is cached once both sides list 20+ starters."""
    from concurrent.futures import ThreadPoolExecutor
    todo = [(r["game_id"], r["espn"], t) for r in games_rows
            if r["away_score"] and r.get("espn") for t in (r["away_team"], r["home_team"])
            if len(cache.get(r["game_id"], {}).get(t, [])) < 20 and t in ESPN_TEAM]
    def one(job):
        gid, eid, team = job
        for _ in range(3):
            try:
                d = fetch_json(ESPN_ROSTER.format(e=eid, t=ESPN_TEAM[team]))
                return gid, team, [str(x["playerId"]) for x in d.get("entries", []) if x.get("starter")]
            except Exception:
                pass
        return gid, team, None
    out = {g: dict(v) for g, v in cache.items()}
    with ThreadPoolExecutor(8) as ex:
        for gid, team, ids in ex.map(one, todo):
            if ids:
                out.setdefault(gid, {})[team] = ids
    failed = sum(1 for g, v in out.items() for t in v if len(v[t]) < 20)
    print(f"ESPN starters: fetched {len(todo)} lineups, {failed} short", file=sys.stderr)
    return out

_CACHE = {}
def fetch_cached(url):
    if url not in _CACHE:
        _CACHE[url] = fetch_csv(url)
    return _CACHE[url]

ESPN_RANKINGS = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cfbsundays-build"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def ap_top(schools, n=3):
    """Top n of the current AP poll, mapped to our school names. Returns
    None on any failure so the caller keeps the previous value."""
    import unicodedata
    def key(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]", "", t.lower())
    lookup = {}
    for s in schools:
        for t in [s["name"], *s.get("alias", [])]:
            lookup.setdefault(key(t), s["name"])
    try:
        data = fetch_json(ESPN_RANKINGS)
        polls = data.get("rankings", [])
        ap = next((p for p in polls if "AP" in (p.get("name", "") + p.get("shortName", ""))), None)
        if not ap:
            return None
        out = []
        for r in sorted(ap.get("ranks", []), key=lambda r: r.get("current", 99)):
            t = r.get("team", {})
            for cand in (t.get("location"), t.get("nickname"), t.get("shortDisplayName"), t.get("displayName")):
                if cand and key(cand) in lookup:
                    out.append(lookup[key(cand)]); break
            if len(out) == n:
                break
        if len(out) < n:
            return None
        return {"ap": out, "apWeek": ap.get("headline") or ap.get("occurrence", {}).get("displayValue", "")}
    except Exception as e:
        print("AP poll fetch failed:", e, file=sys.stderr)
        return None

def fetch_csv(url):
    print("fetching", url, file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "cfbsundays-build"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return list(csv.DictReader(io.TextIOWrapper(r, encoding="utf-8")))

KEEP_STATUS = {"ACT", "RES", "INA", "DEV", "TRT"}
NO_COLLEGE = "No college"

# Earlier college stops missing from nflverse, by gsis id. Each school is
# added after the player's listed schools (the final school stays first).
EXTRA_COLLEGES = {
    "00-0036945": ["Georgia"],      # Justin Fields: Georgia 2018, then Ohio State
}

# Schools mostly known by a short form display that form everywhere;
# the formal name stays searchable as an alias.
RENAME = {
    "Mississippi": "Ole Miss", "California": "Cal", "Pittsburgh": "Pitt",
    "N.C. State": "NC State", "Southern Mississippi": "Southern Miss",
    "Connecticut": "UConn", "Texas-San Antonio": "UTSA", "Texas-El Paso": "UTEP",
    "Florida International": "FIU", "Florida Atlantic": "FAU",
    "Appalachian State": "App State", "Miami (Ohio)": "Miami (OH)",
    # duplicates and long official forms in the roster feed
    "Louisiana-Lafayette": "Louisiana", "University of South Florida": "South Florida",
    "UMass Amherst": "UMass", "Middle Tennessee State": "Middle Tennessee",
    "Texas State-San Marcos": "Texas State", "Jackson State University": "Jackson State",
    # the same school under two names across seasons (mostly the master player file)
    "Brigham Young": "BYU", "Texas Christian": "TCU", "Alabama-Birmingham": "UAB",
    "Mount Union College": "Mount Union", "California Lutheran University": "California Lutheran",
    "University of Indianapolis": "Indianapolis", "Tennessee-Chattanooga": "Chattanooga",
    "Tennessee-Martin": "UT Martin", "No College": NO_COLLEGE, "Unknown": NO_COLLEGE,
}

ALIASES = {
    NO_COLLEGE: ["None", "No school", "Didn't play college", "Never played college", "Did not attend",
                 "International", "International Pathway", "Intl", "Overseas", "Rugby", "N/A"],
    "Georgia": ["UGA", "Dawgs", "Bulldogs", "Go Dawgs"],
    "Ole Miss": ["Rebels"],
    "Alabama": ["Bama", "Crimson Tide", "Tide", "Roll Tide"],
    "Ohio State": ["OSU", "Buckeyes", "tOSU"],
    "Oklahoma State": ["OSU", "Pokes", "Cowboys"],
    "Texas A&M": ["A&M", "TAMU", "aTm", "Aggies"],
    "NC State": ["NCSU", "Wolfpack"],
    "North Carolina": ["UNC", "Tar Heels", "Carolina", "Heels"],
    "South Carolina": ["Gamecocks", "Carolina"],
    "Pitt": ["Panthers"],
    "Cal": ["Golden Bears", "Berkeley"],
    "USC": ["Southern Cal", "Trojans", "Southern California"],
    "Florida": ["UF", "Gators"],
    "Florida State": ["FSU", "Seminoles", "Noles"],
    "Tennessee": ["Vols", "Volunteers", "UT", "Rocky Top"],
    "Texas": ["UT", "Longhorns", "Horns", "Hook Em"],
    "LSU": ["Tigers", "Louisiana State", "Geaux Tigers"],
    "Auburn": ["AU", "Tigers", "War Eagle", "Plains"],
    "Clemson": ["Tigers", "Death Valley"],
    "Missouri": ["Mizzou", "Tigers"],
    "Michigan": ["UM", "Wolverines", "Big Blue"],
    "Michigan State": ["MSU", "Spartans", "Sparty"],
    "Penn State": ["PSU", "Nittany Lions"],
    "Notre Dame": ["ND", "Irish", "Fighting Irish"],
    "Oklahoma": ["OU", "Sooners", "Boomer"],
    "Oregon": ["UO", "Ducks"],
    "Washington": ["UW", "Huskies", "UDub"],
    "Nebraska": ["Huskers", "Cornhuskers"],
    "Wisconsin": ["Badgers", "Wisco"],
    "Iowa": ["Hawkeyes"],
    "Kentucky": ["UK", "Wildcats", "Cats"],
    "Arizona": ["Zona", "Wildcats"],
    "Arizona State": ["ASU", "Sun Devils"],
    "Kansas State": ["K-State", "KSU", "Wildcats"],
    "Kansas": ["KU", "Jayhawks"],
    "TCU": ["Horned Frogs", "Texas Christian", "Frogs"],
    "Baylor": ["Bears"],
    "Texas Tech": ["TTU", "Red Raiders", "Tech"],
    "West Virginia": ["WVU", "Mountaineers", "Eers"],
    "Virginia Tech": ["VT", "Hokies", "Tech"],
    "Virginia": ["UVA", "Cavaliers", "Hoos", "Wahoos"],
    "Miami": ["The U", "Canes", "Hurricanes", "Miami FL"],
    "Louisville": ["Cards", "Cardinals", "UL"],
    "Mississippi State": ["Miss State", "MSU", "Bulldogs", "Hail State"],
    "Arkansas": ["Hogs", "Razorbacks", "Woo Pig"],
    "Vanderbilt": ["Vandy", "Commodores", "Dores"],
    "Stanford": ["Cardinal"],
    "UCLA": ["Bruins"],
    "Colorado": ["CU", "Buffs", "Buffaloes"],
    "Utah": ["Utes"],
    "BYU": ["Brigham Young", "Cougars"],
    "Boise State": ["Broncos"],
    "Georgia Tech": ["GT", "Yellow Jackets", "Jackets", "Tech"],
    "Minnesota": ["Gophers", "Golden Gophers"],
    "Illinois": ["Illini", "Fighting Illini"],
    "Indiana": ["IU", "Hoosiers"],
    "Purdue": ["Boilermakers", "Boilers"],
    "Iowa State": ["ISU", "Cyclones", "Clones"],
    "Oregon State": ["Beavers", "Beavs"],
    "Washington State": ["Wazzu", "WSU", "Cougars", "Cougs"],
    "Houston": ["UH", "Coogs", "Cougars"],
    "Cincinnati": ["Cincy", "Bearcats", "UC"],
    "UCF": ["Central Florida", "Knights"],
    "SMU": ["Southern Methodist", "Mustangs", "Ponies"],
    "Duke": ["Blue Devils"],
    "Wake Forest": ["Wake", "Demon Deacons", "Deacs"],
    "Boston College": ["BC", "Eagles"],
    "Syracuse": ["Cuse", "Orange"],
    "Maryland": ["UMD", "Terps", "Terrapins"],
    "Rutgers": ["Scarlet Knights", "RU"],
    "Northwestern": ["Wildcats", "NU"],
    "Navy": ["Midshipmen", "Mids"],
    "Air Force": ["Falcons"],
    "Memphis": ["Tigers"],
    "Tulane": ["Green Wave"],
    "South Florida": ["USF", "Bulls"],
    "App State": ["Mountaineers", "App"],
    "Coastal Carolina": ["Coastal", "Chanticleers", "Chants"],
    "James Madison": ["JMU", "Dukes"],
    "Liberty": ["Flames"],
    "Fresno State": ["Bulldogs"],
    "San Diego State": ["SDSU", "Aztecs"],
    "UNLV": ["Rebels", "Rebs"],
    "Jackson State": ["JSU", "Thee I Love"],
    "Texas State": ["Bobcats", "TXST"],
    "Toledo": ["Rockets"],
    "Tulsa": ["Golden Hurricane"],
    "Troy": ["Trojans"],
    "Marshall": ["Thundering Herd", "Herd"],
    "Army": ["Black Knights", "West Point"],
    "Temple": ["Owls"],
    "East Carolina": ["ECU", "Pirates"],
    "Western Kentucky": ["WKU", "Hilltoppers", "Tops"],
    "Middle Tennessee": ["MTSU", "Blue Raiders"],
    "Georgia Southern": ["GSU", "Eagles", "Georgia Southern Eagles"],
    "Georgia State": ["GSU", "Panthers"],
    "Louisiana": ["UL", "Ragin Cajuns", "Cajuns", "Louisiana-Lafayette", "ULL"],
    "Louisiana Tech": ["La Tech", "Bulldogs"],
    "Southern Miss": ["USM", "Golden Eagles"],
    "Penn": ["UPenn", "Quakers", "Pennsylvania"],
    "UConn": ["Huskies"],
    "UMass": ["Massachusetts", "Minutemen"],
    "UAB": ["Alabama-Birmingham", "Blazers"],
    "UTSA": ["Roadrunners"],
    "UTEP": ["Miners"],
    "Nevada": ["Wolf Pack"],
    "Hawaii": ["Rainbow Warriors", "Bows"],
    "San Jose State": ["SJSU", "Spartans"],
    "Wyoming": ["Cowboys", "Pokes"],
    "Colorado State": ["CSU", "Rams"],
    "Utah State": ["USU", "Aggies"],
    "New Mexico": ["UNM", "Lobos"],
    "North Dakota State": ["NDSU", "Bison"],
    "South Dakota State": ["SDSU", "Jackrabbits", "Jacks"],
    "Montana State": ["Bobcats"],
    "Sacramento State": ["Sac State", "Hornets"],
    "Incarnate Word": ["UIW", "Cardinals"],
    "Holy Cross": ["Crusaders"],
    "Delaware": ["Blue Hens", "UD"],
    "Villanova": ["Nova", "Wildcats"],
    "William & Mary": ["Tribe", "W&M"],
    "Old Dominion": ["ODU", "Monarchs"],
    "Charlotte": ["49ers", "UNCC"],
    "FAU": ["Owls"],
    "FIU": ["Panthers"],
    "Kent State": ["Golden Flashes"],
    "Bowling Green": ["BGSU", "Falcons"],
    "Ball State": ["Cardinals"],
    "Ohio": ["Bobcats", "OU"],
    "Miami (OH)": ["Miami OH", "RedHawks", "Miami of Ohio"],
    "Buffalo": ["UB", "Bulls"],
    "Akron": ["Zips"],
    "Eastern Michigan": ["EMU", "Eagles"],
    "Western Michigan": ["WMU", "Broncos"],
    "Central Michigan": ["CMU", "Chippewas", "Chips"],
    "Northern Illinois": ["NIU", "Huskies"],
    "North Texas": ["UNT", "Mean Green"],
    "Rice": ["Owls"],
    "Idaho": ["Vandals"],
    "Montana": ["Griz", "Grizzlies"],
    "Youngstown State": ["YSU", "Penguins"],
    "South Alabama": ["USA", "Jaguars", "Jags"],
    "Arkansas State": ["A-State", "Red Wolves"],
}

def norm_name(n):
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?$", "", n.strip().lower())
    return re.sub(r"[^a-z]", "", n)

def main(yr=SEASON, archive=False):
    src = sources(yr)
    out = os.path.join(ARCHIVE, str(yr)) if archive else OUT
    os.makedirs(out, exist_ok=True)
    roster_rows = fetch_csv(src["roster"])
    stats_rows = fetch_csv(src["stats"])
    snaps_rows = fetch_csv(src["snaps"])
    depth_rows = [] if archive else fetch_csv(src["depth"])
    games_rows = fetch_cached(GAMES_URL)
    draft_rows = fetch_cached(DRAFT_URL)
    draft = {r["gsis_id"]: r for r in draft_rows if r.get("gsis_id")}
    # master player file: fills college, entry year and PFR id gaps in older rosters
    master = {r["gsis_id"]: r for r in fetch_cached(PLAYERS_URL) if r.get("gsis_id")}
    had_stats = {r["player_id"] for r in stats_rows if r["season_type"] in ("REG", "POST")}

    # ---- rosters: dedupe by player, keep latest roster week ----
    players, pfr_to_pid, name_team_to_pid = {}, {}, {}
    ever_act = set()
    espn_to_pid = {}
    for m in master.values():
        if m.get("pfr_id") and archive:
            pfr_to_pid[m["pfr_id"]] = m["gsis_id"]
        if m.get("espn_id"):
            espn_to_pid[m["espn_id"]] = m["gsis_id"]
    for r in roster_rows:
        pid = r["gsis_id"] or r["smart_id"]
        if not pid:
            continue
        if r["pfr_id"] and r["gsis_id"]:
            pfr_to_pid[r["pfr_id"]] = r["gsis_id"]
        if r["gsis_id"]:
            name_team_to_pid[(norm_name(r["full_name"]), r["team"])] = r["gsis_id"]
            if r.get("espn_id"):
                espn_to_pid[r["espn_id"]] = r["gsis_id"]
        wk = int(r["week"] or 0)
        if archive:
            if r["status"] == "ACT":
                ever_act.add(pid)
            # past seasons: keep the latest roster spot he held, not a later cut
            keep = r["status"] in KEEP_STATUS
            cur = players.get(pid)
            if cur and (cur["_keep"], cur["_wk"]) >= (keep, wk):
                continue
        elif pid in players and players[pid]["_wk"] >= wk:
            continue
        m = master.get(r["gsis_id"], {})
        # archived seasons prefer the master file (fuller transfer lists);
        # the current season trusts the roster and fills gaps from the master
        college = (m.get("college_name") or r["college"]) if archive else (r["college"] or m.get("college_name"))
        # unescape first: the master file has "Texas A&amp;M", which split into two schools
        colleges = []
        for c in html.unescape(college or "").split(";"):
            c = RENAME.get(c.strip(), c.strip())
            if c and c not in colleges:
                colleges.append(c)
        colleges += [c for c in EXTRA_COLLEGES.get(r["gsis_id"], []) if c not in colleges]
        if not colleges:
            colleges = [NO_COLLEGE]   # mostly International Pathway players
        entry = r["entry_year"] or m.get("rookie_season") or ""
        players[pid] = {"_wk": wk, "name": r["full_name"], "team": r["team"],
                        "pos": r["position"], "status": r["status"],
                        "jersey": r["jersey_number"], "colleges": colleges,
                        "entry": int(entry) if entry else None}
        if archive:
            players[pid]["_keep"] = r["status"] in KEEP_STATUS

    if archive:
        # a season in review: anyone active at any point (or with a stat line) counts as active
        for pid, p in players.items():
            if pid in ever_act or pid in had_stats:
                p["status"] = "ACT"
    active = {pid: p for pid, p in players.items()
              if p["status"] in KEEP_STATUS and p["colleges"]}

    # ---- schools + aliases ----
    school_players = defaultdict(list)
    for p in active.values():
        for i, c in enumerate(p["colleges"]):
            school_players[c].append(i == 0)
    inv = {v: k for k, v in RENAME.items()}
    schools = []
    for name, flags in school_players.items():
        s = {"name": name, "count": len(flags), "primary": sum(flags)}
        a = list(ALIASES.get(name, []))
        if name in inv and inv[name] not in a:
            a.append(inv[name])
        if a:
            s["alias"] = a
        schools.append(s)
    schools.sort(key=lambda x: -x["count"])

    # ---- weekly + season stats ----
    STAT_FIELDS = {
        "passing_yards": "py", "passing_tds": "ptd", "passing_interceptions": "int",
        "completions": "cmp", "attempts": "att",
        "rushing_yards": "ry", "rushing_tds": "rtd", "carries": "car",
        "receiving_yards": "recy", "receiving_tds": "rectd",
        "receptions": "rec", "targets": "tgt",
        "def_tackles_solo": "tk", "def_tackle_assists": "ast", "def_sacks": "sk",
        "def_interceptions": "dint", "def_pass_defended": "pd",
        "fg_made": "fgm", "fg_att": "fga", "pat_made": "xpm",
        "fantasy_points_ppr": "fp", "fantasy_points": "fs",
    }
    weekly = defaultdict(dict)
    wk_team = defaultdict(dict)    # pid -> {week: team}, to place traded players in the right games
    season = defaultdict(lambda: defaultdict(float))
    post_weekly = defaultdict(dict)
    post_season = defaultdict(lambda: defaultdict(float))
    for r in stats_rows:
        pid = r["player_id"]
        if pid not in active or r["season_type"] not in ("REG", "POST"):
            continue
        post = r["season_type"] == "POST"
        wk_map, sn_map = (post_weekly, post_season) if post else (weekly, season)
        line = {}
        for src, dst in STAT_FIELDS.items():
            v = r.get(src) or ""
            if v and float(v) != 0:
                num = float(v)
                line[dst] = int(num) if num == int(num) else num
                sn_map[pid][dst] += num
        line["opp"] = r["opponent_team"]
        if r.get("team"):
            wk_team[pid][int(r["week"])] = r["team"]
        wk_map[pid][int(r["week"])] = line

    # ---- starters from snap counts; specialists count by games played ----
    snap_acc = defaultdict(lambda: {"off": [], "def": []})
    played = defaultdict(set)      # pid -> weeks with any offense, defense or special-teams snap
    for r in snaps_rows:
        pid = pfr_to_pid.get(r["pfr_player_id"]) or \
            name_team_to_pid.get((norm_name(r["player"]), r["team"]))
        if not pid or pid not in active:
            continue
        if any(float(r.get(k) or 0) > 0 for k in ("offense_snaps", "defense_snaps", "st_snaps")):
            played[pid].add(int(r["week"]))
        if r["game_type"] != "REG":
            continue
        snap_acc[pid]["off"].append((int(r["week"]), float(r["offense_pct"] or 0)))
        snap_acc[pid]["def"].append((int(r["week"]), float(r["defense_pct"] or 0)))
    # Starters. Each game: ESPN's starting lineup (on the field for the first
    # snap). Season: at each position group on each team, the usual number of
    # starters (most starts first) plus anyone else who started at least a
    # quarter of the team's games, so splits, benchings and long fill-ins count.
    # Kickers and punters count after two games. If ESPN is unreachable, fall
    # back to 50%+ of snaps.
    POS_GROUP = {"T": "OL", "G": "OL", "C": "OL", "OT": "OL", "OG": "OL", "OL": "OL",
                 "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL", "EDGE": "DL",
                 "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB",
                 "CB": "DB", "S": "DB", "FS": "DB", "SS": "DB", "DB": "DB",
                 "QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE",
                 "K": "K", "P": "P", "LS": "ST"}
    season_games = [r for r in games_rows if r["season"] == str(yr)]
    week_of = {r["game_id"]: int(r["week"]) for r in season_games}
    regular = {r["game_id"] for r in season_games if r["game_type"] == "REG"}
    cache = {}
    if not archive:
        try:
            cache = fetch_json(f"{DOMAIN}/data/starts.json")
        except Exception as e:
            print("no starts cache:", e, file=sys.stderr)
    starts_raw = espn_starts(season_games, cache) if not os.environ.get("NO_ESPN") else {}
    game_starts = defaultdict(list)            # pid -> [week, ...]
    team_starts = defaultdict(lambda: defaultdict(int))   # (team, grp) -> pid -> starts
    team_games = defaultdict(int)              # team -> regular-season games with a lineup
    unmapped = 0
    for gid, sides in starts_raw.items():
        if gid not in week_of:
            continue
        for team, ids in sides.items():
            per = defaultdict(int)
            for eid in ids:
                pid = espn_to_pid.get(eid)
                if not pid:
                    unmapped += 1
                    continue
                game_starts[pid].append(week_of[gid])
                wk_team[pid][week_of[gid]] = team
                if pid in active and gid in regular:   # season starters: regular season only
                    grp = POS_GROUP.get(active[pid]["pos"], active[pid]["pos"])
                    team_starts[(team, grp)][pid] += 1
                    per[grp] += 1
            if gid in regular:
                team_games[team] += 1
    print(f"starts mapped for {len(game_starts)} players, {unmapped} unmapped", file=sys.stderr)
    starters = set()
    # The usual number of starters at the spot (most starts first, ties go in
    # together), plus anyone else who started at least a quarter of the team's games.
    for key, counts in team_starts.items():
        games = team_games[key[0]]
        n = max(1, round(sum(counts.values()) / games)) if games else 1
        chosen = 0
        for c in sorted(set(counts.values()), reverse=True):
            if chosen >= n and c < 0.25 * games:
                break
            tied = [pid for pid, v in counts.items() if v == c]
            starters.update(tied)
            chosen += len(tied)
    for pid, a in snap_acc.items():
        if len(a["off"]) < 2:
            continue
        if active[pid]["pos"] in ("K", "P"):
            starters.add(pid)
        elif not starts_raw:
            off = [v for _, v in a["off"]]
            dfn = [v for _, v in a["def"]]
            if max(statistics.mean(off), statistics.mean(dfn)) >= 0.5:
                starters.add(pid)

    # ---- depth charts: latest snapshot, best non-ST slot per player ----
    latest = max((r["dt"] for r in depth_rows), default=None)
    depth = {}
    for r in depth_rows:
        if r["dt"] != latest:
            continue
        pid = r["gsis_id"]
        if pid not in active:
            continue
        is_st = "Special" in r["pos_grp"] or r["pos_grp"].startswith("ST")
        cand = (is_st, int(r["pos_rank"] or 99), r["pos_abb"])
        cur = depth.get(pid)
        if cur is None or cand[:2] < cur[:2]:
            depth[pid] = cand

    # ---- players.json ----
    pout = {}
    for pid, p in active.items():
        row = {"n": p["name"], "t": p["team"], "p": p["pos"], "s": p["status"],
               "j": p["jersey"], "c": p["colleges"]}
        if pid in starters:
            row["st"] = 1
        if game_starts.get(pid):
            row["gs"] = sorted(set(game_starts[pid]))
        # weeks he got on the field: snap counts, plus any week he started or had a stat line
        pw = played.get(pid, set()) | set(game_starts.get(pid, [])) | set(weekly.get(pid, {})) | set(post_weekly.get(pid, {}))
        if pw:
            row["pw"] = sorted(pw)
        # team history for players who changed teams mid-season: [[from_week, team], ...]
        hist = []
        for w in sorted(wk_team.get(pid, {})):
            t = wk_team[pid][w]
            if not hist or hist[-1][1] != t:
                hist.append([w, t])
        if len({t for _, t in hist} | {p["team"]}) > 1:
            row["tm"] = hist
        if pid in depth:
            _, rank, abb = depth[pid]
            row["d"] = f"{abb}{rank}"
        # conference of each college stop in the player's season there:
        # final school = entry year - 1; earlier stops estimated at entry - 2
        ey = p["entry"]
        if ey:
            row["ey"] = ey
            row["cf"] = [conference(c, ey - 1 if i == 0 else ey - 2)
                         for i, c in enumerate(p["colleges"])]
        d = draft.get(pid)
        if d and d.get("round"):
            row["dr"] = int(d["round"]); row["dp"] = int(d["pick"])
            row["dy"] = int(d["season"]); row["dt"] = d["team"]
        pout[pid] = row

    # ---- stats.json ----
    stats_out = {}
    for pid in weekly:
        tot = {k: (int(v) if v == int(v) else round(v, 1))
               for k, v in season[pid].items()}
        stats_out[pid] = {"w": weekly[pid], "s": tot, "g": len(weekly[pid])}

    # ---- playoffs.json (empty until POST stats exist) ----
    post_out = {}
    for pid in post_weekly:
        tot = {k: (int(v) if v == int(v) else round(v, 1))
               for k, v in post_season[pid].items()}
        post_out[pid] = {"w": post_weekly[pid], "s": tot, "g": len(post_weekly[pid])}

    # ---- games.json ----
    games = [{"id": r["game_id"], "wk": int(r["week"]), "type": r["game_type"],
              "date": r["gameday"], "time": r["gametime"],
              "away": r["away_team"], "home": r["home_team"],
              "as": r["away_score"], "hs": r["home_score"]}
             for r in games_rows if r["season"] == str(yr)]
    games.sort(key=lambda g: (g["wk"], g["date"], g["time"]))

    # ---- rankings.json (credit = school player finished at) ----
    rank = defaultdict(lambda: defaultdict(float))
    for pid, p in active.items():
        sc = p["colleges"][0]
        rank["total"][sc] += 1
        if p["status"] == "ACT":
            rank["active"][sc] += 1
            grp = POS_GROUP.get(p["pos"], p["pos"])
            rank[f"pos_{grp}"][sc] += 1
            if pid in starters:
                rank["starters"][sc] += 1
                rank[f"start_{grp}"][sc] += 1
        s = season.get(pid, {})
        rank["py"][sc] += s.get("py", 0)
        rank["ry"][sc] += s.get("ry", 0)
        rank["recy"][sc] += s.get("recy", 0)
        rank["sk"][sc] += s.get("sk", 0)
        rank["tkl"][sc] += s.get("tk", 0) + s.get("ast", 0)
        rank["dint"][sc] += s.get("dint", 0)
        rank["tds"][sc] += s.get("rtd", 0) + s.get("rectd", 0)
        rank["fgm"][sc] += s.get("fgm", 0)
    rk_out = {}
    for cat, vals in rank.items():
        rows = sorted(((s, v) for s, v in vals.items() if v > 0),
                      key=lambda x: (-x[1], x[0]))
        rk_out[cat] = [[s, int(v) if v == int(v) else round(v, 1)] for s, v in rows]

    if archive:
        for name, obj in [("schools", schools), ("players", pout), ("games", games),
                          ("stats", stats_out), ("playoffs", post_out)]:
            json.dump(obj, open(os.path.join(out, f"{name}.json"), "w"), separators=(",", ":"))
        print(f"archive {yr}: players={len(active)} starters={len(starters)} "
              f"with stats={len(stats_out)} games={len(games)}", file=sys.stderr)
        return

    # current AP top 3 for the search box examples; keep last good copy on failure
    meta_path = os.path.join(OUT, "meta.json")
    try:
        meta = json.load(open(meta_path))
    except Exception:
        meta = {"ap": ["Miami", "Ohio State", "Georgia"], "apWeek": "fallback"}
    fresh = ap_top(schools)
    if fresh:
        meta.update(fresh)
        print("AP top 3:", fresh["ap"], file=sys.stderr)
    meta["season"] = yr
    json.dump(meta, open(meta_path, "w"), separators=(",", ":"))

    for name, obj in [("schools", schools), ("players", pout), ("games", games),
                      ("stats", stats_out), ("rankings", rk_out), ("playoffs", post_out),
                      ("starts", starts_raw)]:
        path = os.path.join(OUT, f"{name}.json")
        json.dump(obj, open(path, "w"), separators=(",", ":"))
        print(f"{name}.json {os.path.getsize(path)//1024} KB", file=sys.stderr)
    prerender(schools, active, starters, depth)
    print(f"players={len(active)} starters={len(starters)} games={len(games)}",
          file=sys.stderr)



DOMAIN = "https://cfbsundays.com"

def slugify(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")

def prerender(schools, active, starters, depth):
    """Static, crawlable page per school + sitemap. Targets searches like
    'georgia players in the NFL'. The app page stays the product; these
    pages exist for search engines and deep links."""
    import datetime, html
    sdir = os.path.join(OUT, "..", "s")
    os.makedirs(sdir, exist_ok=True)
    today = datetime.date.today().isoformat()
    by_school = defaultdict(lambda: {"primary": [], "also": []})
    for pid, p in active.items():
        for i, c in enumerate(p["colleges"]):
            by_school[c]["primary" if i == 0 else "also"].append((pid, p))
    urls = [f"{DOMAIN}/"]
    for s in schools:
        if s["count"] < 5:
            continue
        name = s["name"]
        slug = slugify(name)
        e = html.escape
        alias = ", ".join(s.get("alias", [])[:3])
        rows = []
        for pid, p in sorted(by_school[name]["primary"],
                             key=lambda x: (x[1]["status"] != "ACT", x[1]["name"])):
            role = f'{p["pos"]}, {p["team"]}'
            extra = []
            if pid in depth:
                extra.append(depth[pid][2] + str(depth[pid][1]))
            if pid in starters:
                extra.append("starter")
            if p["status"] != "ACT":
                extra.append({"RES": "IR", "DEV": "practice squad",
                              "INA": "inactive", "TRT": "returning"}.get(p["status"], ""))
            rows.append(f"<li><strong>{e(p['name'])}</strong> ({e(role)}"
                        f"{', ' + e(', '.join(x for x in extra if x)) if any(extra) else ''})</li>")
        also = [f"<li><strong>{e(p['name'])}</strong> ({e(p['pos'])}, {e(p['team'])}), "
                f"finished at {e(p['colleges'][0])}</li>"
                for pid, p in sorted(by_school[name]["also"], key=lambda x: x[1]["name"])]
        nc = name == NO_COLLEGE
        title = (f"NFL players who didn't play college football ({SEASON})" if nc
                 else f"{name} players in the NFL ({SEASON})")
        desc = (f"All {s['count']} NFL players in {SEASON} with no college listed, mostly "
                f"International Pathway players: teams, positions and depth chart spots. Updated daily."
                if nc else
                f"All {s['count']} {name}{' (' + alias + ')' if alias else ''} players "
                f"in the NFL in {SEASON}: current teams, positions, depth chart spots, "
                f"and who transferred in or out. Updated daily.")
        intro = (f"<strong>{s['count']}</strong> players in the NFL in {SEASON} have no college "
                 f"listed in NFL roster records, including practice squads and injured reserve. "
                 f"Most came through the International Pathway; a few may simply be missing "
                 f"from the records. Updated {today}." if nc else
                 f"{e(name)}{' (' + e(alias) + ')' if alias else ''} has <strong>{s['count']}</strong> players\n"
                 f"in the NFL in {SEASON}, including practice squads and injured reserve.\n"
                 f"Finished their college career at {e(name)}: <strong>{s['primary']}</strong>.\n"
                 f"Updated {today} from NFL roster data.")
        page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} - CFB Sundays</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{DOMAIN}/s/{slug}.html">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:680px;margin:0 auto;padding:0 16px 32px;color:#0c1526;background:#e4e9f0}}
@media(prefers-color-scheme:dark){{body{{color:#e7edf8;background:#090f1d}}a{{color:#6f9bff}}}}
a{{color:#1546b8;text-underline-offset:3px}}li{{margin:4px 0}}
header{{margin:0 -16px 16px;padding:14px 16px;background:#1546b8;border-bottom:3px solid #ffc629}}
header a{{color:#fff;font-weight:700}}
h1{{font-style:oblique 9deg;text-transform:uppercase;line-height:1.1}}</style>
<script data-goatcounter="https://cfbsundays.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script></head><body>
<header><a href="/">&larr; CFB Sundays: see these players by NFL game, live stats and rankings</a></header>
<h1>{e(title)}</h1>
<p>{intro}</p>
<h2>{'Players' if nc else 'Players who finished at ' + e(name)}</h2><ul>{''.join(rows)}</ul>
{'<h2>Played at ' + e(name) + ', finished elsewhere</h2><ul>' + ''.join(also) + '</ul>' if also else ''}
<p><a href="/">Track {'these' if nc else e(name)} players game by game on CFB Sundays</a>. Pick your schools
and see who is in each NFL game this week with per-game and season stats.</p>
<p>Data: nflverse (free, open NFL data) and ESPN starting lineups. A starter is one of the most-started
players at his position on his team this season, or started at least a quarter of its games.</p>
</body></html>"""
        open(os.path.join(sdir, f"{slug}.html"), "w").write(page)
        urls.append(f"{DOMAIN}/s/{slug}.html")
    sm = "\n".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    open(os.path.join(OUT, "..", "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "\n</urlset>")
    open(os.path.join(OUT, "..", "robots.txt"), "w").write(
        # Search engines may fetch everything (they render the page with its data).
        # Every other crawler skips the raw data files, which have no search value
        # and are the heaviest thing to fetch. Only polite bots obey this.
        f"User-agent: Googlebot\nUser-agent: Bingbot\nAllow: /\n\n"
        f"User-agent: *\nDisallow: /data/\nDisallow: /archive/\nAllow: /\n\n"
        f"Sitemap: {DOMAIN}/sitemap.xml\n")
    print(f"prerendered {len(urls)-1} school pages + sitemap", file=sys.stderr)
def write_season_list():
    yrs = sorted((int(d) for d in os.listdir(ARCHIVE) if d.isdigit()), reverse=True) \
        if os.path.isdir(ARCHIVE) else []
    json.dump(yrs, open(os.path.join(ARCHIVE, "seasons.json"), "w"))
    print("archived seasons:", yrs, file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--archive":
        # "all" = every finished season: FIRST_ARCHIVE through SEASON - 1
        rng = f"{FIRST_ARCHIVE}-{SEASON - 1}" if sys.argv[2] == "all" else sys.argv[2]
        a, _, b = rng.partition("-")
        for yr in range(int(a), int(b or a) + 1):
            main(yr, archive=True)
        write_season_list()
    else:
        main()
