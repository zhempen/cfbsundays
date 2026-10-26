#!/usr/bin/env python3
"""CFB Sundays data pipeline.

Downloads free nflverse data (rosters, weekly stats, snap counts, depth
charts, schedule) and writes the small JSON files the static site reads.
Run from the repo root: python3 scripts/build.py
"""
import csv, io, json, os, re, statistics, sys, urllib.request
from collections import defaultdict

SEASON = int(os.environ.get("SEASON", "2026"))
OUT = os.path.join(os.path.dirname(__file__), "..", "site", "data")
os.makedirs(OUT, exist_ok=True)

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
SOURCES = {
    "roster": f"{NFLVERSE}/rosters/roster_{SEASON}.csv",
    "stats": f"{NFLVERSE}/stats_player/stats_player_week_{SEASON}.csv",
    "snaps": f"{NFLVERSE}/snap_counts/snap_counts_{SEASON}.csv",
    "depth": f"{NFLVERSE}/depth_charts/depth_charts_{SEASON}.csv",
    "games": "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",
}

def fetch_csv(url):
    print("fetching", url, file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "cfbsundays-build"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return list(csv.DictReader(io.TextIOWrapper(r, encoding="utf-8")))

KEEP_STATUS = {"ACT", "RES", "INA", "DEV", "TRT"}

# Schools mostly known by a short form display that form everywhere;
# the formal name stays searchable as an alias.
RENAME = {
    "Mississippi": "Ole Miss", "California": "Cal", "Pittsburgh": "Pitt",
    "N.C. State": "NC State", "Southern Mississippi": "Southern Miss",
    "Connecticut": "UConn", "Texas-San Antonio": "UTSA", "Texas-El Paso": "UTEP",
    "Florida International": "FIU", "Florida Atlantic": "FAU",
    "Appalachian State": "App State", "Miami (Ohio)": "Miami (OH)",
}

ALIASES = {
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
    "Georgia Southern": ["GSU", "Eagles", "Southern"],
    "Georgia State": ["GSU", "Panthers"],
    "Louisiana": ["UL", "Ragin Cajuns", "Cajuns", "Louisiana-Lafayette", "ULL"],
    "Louisiana Tech": ["La Tech", "Bulldogs"],
    "Southern Miss": ["USM", "Golden Eagles"],
    "Penn": ["UPenn", "Quakers", "Pennsylvania"],
    "UConn": ["Huskies"],
    "Massachusetts": ["UMass", "Minutemen"],
    "Alabama-Birmingham": ["UAB", "Blazers"],
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

def main():
    roster_rows = fetch_csv(SOURCES["roster"])
    stats_rows = fetch_csv(SOURCES["stats"])
    snaps_rows = fetch_csv(SOURCES["snaps"])
    depth_rows = fetch_csv(SOURCES["depth"])
    games_rows = fetch_csv(SOURCES["games"])

    # ---- rosters: dedupe by player, keep latest roster week ----
    players, pfr_to_pid, name_team_to_pid = {}, {}, {}
    for r in roster_rows:
        pid = r["gsis_id"] or r["smart_id"]
        if not pid:
            continue
        if r["pfr_id"] and r["gsis_id"]:
            pfr_to_pid[r["pfr_id"]] = r["gsis_id"]
        if r["gsis_id"]:
            name_team_to_pid[(norm_name(r["full_name"]), r["team"])] = r["gsis_id"]
        wk = int(r["week"] or 0)
        if pid in players and players[pid]["_wk"] >= wk:
            continue
        colleges = [RENAME.get(c.strip(), c.strip())
                    for c in (r["college"] or "").split(";") if c.strip()]
        players[pid] = {"_wk": wk, "name": r["full_name"], "team": r["team"],
                        "pos": r["position"], "status": r["status"],
                        "jersey": r["jersey_number"], "colleges": colleges}

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
    }
    weekly = defaultdict(dict)
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
        wk_map[pid][int(r["week"])] = line

    # ---- starters from snap counts; specialists count by games played ----
    snap_acc = defaultdict(lambda: {"off": [], "def": []})
    for r in snaps_rows:
        if r["game_type"] != "REG":
            continue
        pid = pfr_to_pid.get(r["pfr_player_id"]) or \
            name_team_to_pid.get((norm_name(r["player"]), r["team"]))
        if not pid or pid not in active:
            continue
        snap_acc[pid]["off"].append(float(r["offense_pct"] or 0))
        snap_acc[pid]["def"].append(float(r["defense_pct"] or 0))
    starters = set()
    for pid, a in snap_acc.items():
        if len(a["off"]) < 2:
            continue
        if active[pid]["pos"] in ("K", "P"):
            starters.add(pid)
        else:
            o = statistics.mean(a["off"])
            d = statistics.mean(a["def"])
            if max(o, d) >= 0.5:
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
        if pid in depth:
            _, rank, abb = depth[pid]
            row["d"] = f"{abb}{rank}"
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
             for r in games_rows if r["season"] == str(SEASON)]
    games.sort(key=lambda g: (g["wk"], g["date"], g["time"]))

    # ---- rankings.json (credit = school player finished at) ----
    POS_GROUP = {"T": "OL", "G": "OL", "C": "OL", "OT": "OL", "OG": "OL", "OL": "OL",
                 "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL", "EDGE": "DL",
                 "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB",
                 "CB": "DB", "S": "DB", "FS": "DB", "SS": "DB", "DB": "DB",
                 "QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE",
                 "K": "K", "P": "P", "LS": "ST"}
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

    for name, obj in [("schools", schools), ("players", pout), ("games", games),
                      ("stats", stats_out), ("rankings", rk_out), ("playoffs", post_out)]:
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
        title = f"{name} players in the NFL ({SEASON})"
        desc = (f"All {s['count']} {name}{' (' + alias + ')' if alias else ''} players "
                f"in the NFL in {SEASON}: current teams, positions, depth chart spots, "
                f"and who transferred in or out. Updated daily.")
        page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} - CFB Sundays</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{DOMAIN}/s/{slug}.html">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:680px;margin:0 auto;padding:16px;color:#1b1b18;background:#f6f5f1}}
@media(prefers-color-scheme:dark){{body{{color:#ece9df;background:#16150f}}a{{color:#d9544a}}}}
a{{color:#a3261e}}li{{margin:4px 0}}</style></head><body>
<p><a href="/">&larr; CFB Sundays: see these players by NFL game, live stats and rankings</a></p>
<h1>{e(title)}</h1>
<p>{e(name)}{' (' + e(alias) + ')' if alias else ''} has <strong>{s['count']}</strong> players
in the NFL in {SEASON}, including practice squads and injured reserve.
Finished their college career at {e(name)}: <strong>{s['primary']}</strong>.
Updated {today} from NFL roster data.</p>
<h2>Players who finished at {e(name)}</h2><ul>{''.join(rows)}</ul>
{'<h2>Played at ' + e(name) + ', finished elsewhere</h2><ul>' + ''.join(also) + '</ul>' if also else ''}
<p><a href="/">Track {e(name)} players game by game on CFB Sundays</a> &mdash; pick your schools,
see who is in each NFL game this week with per-game and season stats.</p>
<p>Data: nflverse (free, open NFL data). A starter averages 50%+ of team snaps over 2+ games.</p>
</body></html>"""
        open(os.path.join(sdir, f"{slug}.html"), "w").write(page)
        urls.append(f"{DOMAIN}/s/{slug}.html")
    sm = "\n".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    open(os.path.join(OUT, "..", "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "\n</urlset>")
    open(os.path.join(OUT, "..", "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    print(f"prerendered {len(urls)-1} school pages + sitemap", file=sys.stderr)
if __name__ == "__main__":
    main()
