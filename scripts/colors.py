#!/usr/bin/env python3
"""Team colors for the site: NFL from nflverse, colleges from ESPN's team list.

Writes site/colors.json  {"nfl": {"PHI": ["#004c54", "#a5acaf"]},
                          "school": {"Georgia": ["#ba0c2f", "#000000"]}}
Colors rarely change, so the file is committed and refreshed by the
archive-build workflow (ESPN isn't reachable from every environment).
Only colors are used on the site, never logos.
"""
import csv, io, json, os, re, sys, unicodedata, urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
NFL_URL = "https://raw.githubusercontent.com/nflverse/nflfastR-data/master/teams_colors_logos.csv"
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=2000"

# our school name -> ESPN "location" where the simple match misses
MANUAL = {
    "Miami": "Miami", "Miami (OH)": "Miami (OH)", "Pitt": "Pittsburgh", "Cal": "California",
    "Ole Miss": "Ole Miss", "NC State": "NC State", "UConn": "UConn", "USC": "USC",
    "App State": "App State", "Southern Miss": "Southern Miss", "FIU": "Florida International",
    "FAU": "Florida Atlantic", "UTSA": "UTSA", "UTEP": "UTEP", "Louisiana": "Louisiana",
    "Louisiana-Monroe": "UL Monroe", "UMass": "Massachusetts", "Hawaii": "Hawai'i",
    "San Jose State": "San José State", "Texas A&M": "Texas A&M",
    # renamed schools and roster spellings that differ from ESPN's
    "Sam Houston State": "Sam Houston", "McNeese State": "McNeese", "Nicholls State": "Nicholls",
    "Grambling State": "Grambling", "Southeastern Louisiana": "SE Louisiana",
    "Stephen F. Austin State": "Stephen F. Austin", "Chattanooga": "Chattanooga", "UT Martin": "UT Martin",
    "Northwestern State (LA)": "Northwestern State", "Towson State": "Towson",
    "Cal Poly (San Luis Obispo)": "Cal Poly", "Texas A&M-Commerce": "East Texas A&M",
    "West Texas State": "West Texas A&M", "Southern Utah State": "Southern Utah",
    "Tennessee Technological Univ": "Tennessee Tech", "Houston Baptist University": "Houston Christian",
    "Mercer University, Atlanta": "Mercer", "Indiana PA,  University of": "Indiana (PA)",
    "Pittsburg State (KS)": "Pittsburg State", "Minn. State-Mankato": "Minnesota State",
    "Grand Valley": "Grand Valley State", "Northeastern University, Mass": "Northeastern",
    "Colorado State (Pueblo)": "CSU Pueblo", "Texas A&M University-Kingsville": "Texas A&M-Kingsville",
    "Northeastern State (Ok)": "Northeastern State", "Wayne State, Mich.": "Wayne State (MI)",
    "University of West Florida": "West Florida", "Nebraska-Omaha": "Omaha",
}

def variants(name):
    """Plain forms of a roster spelling: drop University/College, 'University of X' -> X."""
    n = re.sub(r"\s*\(.*?\)", "", name)
    out = [n]
    out.append(re.sub(r"^University of\s+", "", n))
    out.append(re.sub(r"\s+(University|College|Univ\.?)$", "", n))
    out.append(re.sub(r"\s+State University$", " State", n))
    return out

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cfbsundays-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

def key(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    t = t.lower().replace("&", "and").replace("st.", "state")
    return re.sub(r"[^a-z0-9]", "", t)

def hexc(c):
    c = (c or "").strip().lstrip("#").lower()
    return "#" + c if re.fullmatch(r"[0-9a-f]{6}", c) else None

def our_schools():
    names = {}
    paths = [os.path.join(ROOT, "site", "data", "schools.json")]
    adir = os.path.join(ROOT, "site", "archive")
    if os.path.isdir(adir):
        paths += [os.path.join(adir, d, "schools.json") for d in os.listdir(adir) if d.isdigit()]
    for p in paths:
        try:
            for s in json.load(open(p)):
                names.setdefault(s["name"], set()).update(s.get("alias", []))
        except Exception:
            pass
    return names

def main():
    out = {"nfl": {}, "school": {}}
    for r in csv.DictReader(io.StringIO(get(NFL_URL))):
        cols = [hexc(r.get("team_color")), hexc(r.get("team_color2"))]
        out["nfl"][r["team_abbr"]] = [c for c in cols if c]

    data = json.loads(get(ESPN_URL))
    teams = [t["team"] for t in data["sports"][0]["leagues"][0]["teams"]]
    by_key = {}
    # one pass per field so an exact location ("Miami") always beats another
    # team's short name that happens to match it
    for field in ("location", "displayName", "shortDisplayName", "nickname"):
        for t in teams:
            c1, c2 = hexc(t.get("color")), hexc(t.get("alternateColor"))
            if not c1 or (c1 == "#000000" and not c2):
                continue                  # ESPN placeholder: no real colors on file
            if t.get(field):
                by_key.setdefault(key(t[field]), [c1] + ([c2] if c2 and c2 != c1 else []))

    schools = our_schools()
    missed = []
    for name, aliases in sorted(schools.items()):
        if name == "No college":
            continue
        cands = [MANUAL.get(name), name, *variants(name), *aliases,
                 re.sub(r"\bState\b", "St", name), name.replace("Saint", "St")]
        hit = next((by_key[key(c)] for c in cands if c and key(c) in by_key), None)
        if hit:
            out["school"][name] = hit
        else:
            missed.append(name)

    path = os.path.join(ROOT, "site", "colors.json")
    json.dump(out, open(path, "w"), separators=(",", ":"), sort_keys=True)
    print(f"colors: {len(out['nfl'])} NFL teams, {len(out['school'])} schools matched, "
          f"{len(missed)} without colors", file=sys.stderr)
    print("no colors for:", ", ".join(missed), file=sys.stderr)

if __name__ == "__main__":
    main()
