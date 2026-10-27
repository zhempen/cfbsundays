#!/usr/bin/env python3
"""Tuesday email: one message per active subscriber, covering their schools.

Reads subscribers from the Cloudflare D1 database (REST API), builds each
email from the site's own data files, and sends through Resend's batch API.
A week is sent once: the `sends` table records it, so re-runs do nothing.

Modes (env MODE):
  send    scheduled run; only from 7 AM New York time on, unless FORCE=1
  sample  send the latest week to every active subscriber without recording
          it; refuses if there are more than 3 (for testing with yourself)
  preview no database, no sending; writes sample HTML for the schools in
          PREVIEW_SCHOOLS (comma separated) to PREVIEW_OUT
Env: CLOUDFLARE_API_TOKEN, RESEND_API_KEY, DATA (site URL or local folder).
"""
import datetime, html, json, os, re, sys, urllib.request
from zoneinfo import ZoneInfo

ROOT = os.path.join(os.path.dirname(__file__), "..")
SITE = "https://cfbsundays.com"
DATA = os.environ.get("DATA", SITE)
MODE = os.environ.get("MODE", "send")
FROM = "CFB Sundays <tuesday@mail.cfbsundays.com>"
REPLY_TO = "hello@cfbsundays.com"
RESEND_DAILY_FREE = 100

def worker_conf():
    t = open(os.path.join(ROOT, "worker", "wrangler.toml")).read()
    acct = re.search(r'account_id = "(\w+)"', t).group(1)
    return acct, os.environ.get("WORKER_URL") or open(os.path.join(ROOT, "worker", "URL")).read().strip()

def http(url, data=None, headers=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"),
                                 headers={"User-Agent": "cfbsundays-email", "Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def load(name):
    if DATA.startswith("http"):
        try:
            return http(f"{DATA}/{name}")
        except Exception:
            return {}
    p = os.path.join(DATA, name)
    return json.load(open(p)) if os.path.exists(p) else {}

# ---------- D1 ----------
class D1:
    def __init__(self, acct):
        self.base = f"https://api.cloudflare.com/client/v4/accounts/{acct}/d1/database"
        self.h = {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"}
        dbs = http(f"{self.base}?name=cfbsundays", headers=self.h)["result"]
        self.id = next(d["uuid"] for d in dbs if d["name"] == "cfbsundays")
    def q(self, sql, params=()):
        r = http(f"{self.base}/{self.id}/query", {"sql": sql, "params": list(params)}, self.h)
        return r["result"][0]["results"]

# ---------- content ----------
ROUND = {"WC": "Wild Card round", "DIV": "Divisional round", "CON": "Conference championships", "SB": "Super Bowl"}
# email palette and type, from DESIGN.md (steel light theme; email clients get one theme)
GROUND, PANEL, INK, MUTED, LINE = "#cdd5df", "#edf1f6", "#0c1526", "#3d4a5f", "#aeb9c8"
GOLD, GOLD_INK = "#ffc629", "#1b1400"
FACE = "Saira,'Arial Narrow',Arial,Helvetica,sans-serif"
DISPLAY = f"font-family:{FACE};font-weight:800;font-style:italic;text-transform:uppercase;letter-spacing:.02em;line-height:1.05"
LABEL = f"font-family:{FACE};font-weight:700;font-style:italic;text-transform:uppercase;letter-spacing:.06em;font-size:12px"

# position groups, in the order they appear; roster positions fold into them
GROUPS = [("Quarterbacks", {"QB"}), ("Running backs", {"RB", "FB", "HB"}), ("Wide receivers", {"WR"}),
          ("Tight ends", {"TE"}), ("Offensive line", {"OL", "T", "G", "C", "OT", "OG"}),
          ("Defensive line", {"DL", "DE", "DT", "NT"}), ("Linebackers", {"LB", "OLB", "ILB", "MLB"}),
          ("Defensive backs", {"DB", "CB", "S", "FS", "SS"}), ("Special teams", {"K", "P", "LS"})]
def group_of(pos):
    return next((i for i, (_, ps) in enumerate(GROUPS) if pos in ps), len(GROUPS))

def snap_part(sn):
    """'64 snaps', '64 snaps + 5 ST', or '12 ST snaps'."""
    if not sn:
        return ""
    od, st = sn[0] + sn[1], sn[2]
    if od:
        return f"{od} snaps" + (f" + {st} ST" if st else "")
    return f"{st} ST snaps" if st else ""

def full_line(w, sn):
    """Snaps first, then every stat he has, offense to defense to kicking."""
    w = w or {}
    n = lambda k: w.get(k, 0)
    s = lambda v, word: f"{fmt(v)} {word}{'' if v == 1 else 's'}"
    parts = [snap_part(sn)]
    if n("att"):
        parts.append(f"{n('cmp')}/{n('att')}, {n('py')} pass yds" + (f", {n('ptd')} TD" if n("ptd") else "") + (f", {n('int')} INT" if n("int") else ""))
    if n("car"):
        parts.append(f"{n('car')} car, {n('ry')} rush yds" + (f", {n('rtd')} TD" if n("rtd") else ""))
    if n("rec") or n("recy"):
        parts.append(f"{n('rec')} rec, {n('recy')} yds" + (f", {n('rectd')} TD" if n("rectd") else ""))
    d = [s(tk(w), "tackle")] if tk(w) else []
    if n("sk"):
        d.append(s(n("sk"), "sack"))
    if n("dint"):
        d.append(f"{n('dint')} INT")
    if n("pd"):
        d.append(f"{n('pd')} PD")
    if d:
        parts.append(", ".join(d))
    if n("fga"):
        parts.append(f"{n('fgm')}/{n('fga')} FG")
    if n("xpm"):
        parts.append(f"{n('xpm')} XP")
    return " · ".join(x for x in parts if x)

def ink_for(hexcol):
    """Readable text color on a school color (same rule as the site)."""
    m = re.match(r"^#?([0-9a-fA-F]{6})$", hexcol or "")
    if not m:
        return "#ffffff"
    v = int(m.group(1), 16)
    lum = lambda x: x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4
    r, g, b = (lum((v >> sh & 255) / 255) for sh in (16, 8, 0))
    return "#0c1526" if .2126 * r + .7152 * g + .0722 * b > .36 else "#ffffff"

def tk(w): return w.get("tk", 0) + w.get("ast", 0)
def fmt(v): return int(v) if v == int(v) else v
e = html.escape

def team_for(p, wk, lines):
    if not p.get("tm"):
        return p["t"]
    t = p["tm"][0][1]
    for w, tt in p["tm"]:
        if w <= wk:
            t = tt
    return t

class Week:
    def __init__(self):
        self.players = load("data/players.json")
        stats, post = load("data/stats.json"), load("data/playoffs.json")
        self.games = load("data/games.json")
        self.meta = load("data/meta.json")
        self.colors = load("colors.json") or {"school": {}}
        self.lines = {}                         # pid -> {week: line}
        for src in (stats, post):
            for pid, s in (src or {}).items():
                for wk, line in s.get("w", {}).items():
                    self.lines.setdefault(pid, {})[int(wk)] = line
        self.week = self.latest_done_week()
        g = next((g for g in self.games if g["wk"] == self.week), None)
        self.type = g["type"] if g else "REG"
        self.label = ROUND.get(self.type, f"Week {self.week}")
        self.season = self.meta.get("season")

    def latest_done_week(self):
        """Latest week whose games are all final AND have stat lines for both
        teams (so Monday night is in before anything goes out). Snap counts are
        not waited on: a player with stats but no snaps yet still shows."""
        weeks = sorted({g["wk"] for g in self.games})
        done = []
        for w in weeks:
            gs = [g for g in self.games if g["wk"] == w]
            if not gs or any(g["as"] == "" for g in gs):
                continue
            teams = {team_for(self.players[pid], w, None) for pid, l in self.lines.items()
                     if w in l and pid in self.players}
            if not all(g["away"] in teams and g["home"] in teams for g in gs):
                continue
            done.append(w)
        return done[-1] if done else None

    def school_block(self, sc):
        mine = [(pid, p) for pid, p in self.players.items() if p["c"] and p["c"][0] == sc]
        rows = [(pid, p, self.lines[pid][self.week]) for pid, p in mine
                if self.week in self.lines.get(pid, {})]
        col = (self.colors.get("school", {}).get(sc) or ["#1546b8"])[0]
        sums = {k: sum(r[2].get(k, 0) for r in rows) for k in ("py", "ry", "recy", "ptd", "rtd", "rectd", "sk", "dint")}
        tds = sums["ptd"] + sums["rtd"] + sums["rectd"]
        parts = [(sums["py"], f"{sums['py']:,} pass yds"), (sums["ry"], f"{sums['ry']:,} rush yds"),
                 (sums["recy"], f"{sums['recy']:,} rec yds"), (tds, f"{tds} TD{'s' if tds != 1 else ''}"),
                 (sums["sk"], f"{fmt(sums['sk'])} sack{'s' if sums['sk'] != 1 else ''}"),
                 (sums["dint"], f"{sums['dint']} INT{'s' if sums['dint'] != 1 else ''}")]
        totals = " · ".join(t for v, t in parts if v)
        mute = f"color:{MUTED};font-size:13px"
        col2 = (self.colors.get("school", {}).get(sc) or [col, col])[-1]
        h = [f'<tr><td style="padding:22px 0 4px;border-top:1px solid {LINE}">'
             f'<div style="{DISPLAY};font-size:22px;color:{INK}">'
             f'<span style="display:inline-block;width:0;height:12px;border-left:7px solid {col};border-right:7px solid {col2};margin-right:9px"></span>{e(sc)}</div>']
        t = [f"\n{sc.upper()}"]
        wk = self.week
        on_field = [(pid, p) for pid, p in mine
                    if wk in p.get("pw", []) or wk in p.get("gs", []) or wk in self.lines.get(pid, {})]
        if not on_field:
            h.append(f'<p style="color:{MUTED};margin:6px 0 0">No former players saw the field this week.</p></td></tr>')
            t.append("No former players saw the field this week.")
            return "".join(h), "\n".join(t)
        if totals:
            # a dark score-bug strip; the numbers are "your numbers", so they get the gold
            bug = re.sub(r"(\d[\d,.]*)", r'<b style="color:#ffc629">\1</b>', totals)
            h.append(f'<p style="background:#18264a;border:1px solid #0a1226;border-top-color:#2c3f6e;color:#c9d4ea;font-size:14px;'
                     f'border-radius:3px;padding:6px 10px;margin:8px 0 12px">{bug}</p>')
            t.append(totals)
        # everyone who got on the field, by position: starters first, then most snaps
        ink = ink_for(col)
        badge = (f'<span style="display:inline-block;background:{col};color:{ink};font-size:10px;font-weight:700;'
                 f'letter-spacing:.4px;padding:1px 6px;border-radius:3px;vertical-align:1px">STARTED</span>')
        def order(x):
            pid, p = x
            sn = p.get("sn", {}).get(str(wk)) or [0, 0, 0]
            return (wk not in p.get("gs", []), -(sn[0] + sn[1]), -sn[2], p["n"])
        groups = {}
        for x in on_field:
            groups.setdefault(group_of(x[1]["p"]), []).append(x)
        for gi in sorted(groups):
            lbl = GROUPS[gi][0] if gi < len(GROUPS) else "Other"
            h.append(f'<p style="margin:16px 0 4px;padding-bottom:2px;border-bottom:1px solid {LINE};{LABEL};color:{MUTED}">{lbl}</p>')
            t.append(f"\n{lbl}")
            for pid, p in sorted(groups[gi], key=order):
                team = team_for(p, wk, None)
                started = wk in p.get("gs", [])
                line = full_line(self.lines.get(pid, {}).get(wk), p.get("sn", {}).get(str(wk)))
                also = (f' <span style="display:inline-block;background:#ffe9a8;color:#5c4300;font-size:11px;font-weight:600;'
                        f'padding:0 6px;border-radius:2px">also {e(", ".join(p["c"][1:]))}</span>') if len(p["c"]) > 1 else ""
                h.append(f'<p style="margin:0 0 6px;color:{INK}"><b>{e(p["n"])}</b> <span style="{mute}">{team}</span>{also}'
                         f'{" " + badge if started else ""}{"<br>" + e(line) if line else ""}</p>')
                t.append(f"  {p['n']} ({team}{', also ' + ', '.join(p['c'][1:]) if len(p['c']) > 1 else ''}){' started' if started else ''}" + (f": {line}" if line else ""))
        h.append("</td></tr>")
        return "".join(h), "\n".join(t)

    def email(self, schools, unsub_url):
        blocks = [self.school_block(sc) for sc in schools]
        link = f"{SITE}/?s=" + ",".join(urllib.request.quote(s) for s in schools)
        who = schools[0] if len(schools) == 1 else ", ".join(schools[:-1]) + " and " + schools[-1]
        subject = f"{self.label}: {who} in the pros"
        c = self.colors.get("school", {}).get(schools[0]) or ["#1b1e25", "#c3c9d2"]
        t1, t2 = c[0], c[-1] if len(c) > 1 else "#c3c9d2"
        tink = ink_for(t1)
        html_doc = f"""<!doctype html><html><head><meta name="color-scheme" content="light">
<link href="https://fonts.googleapis.com/css2?family=Saira:ital,wght@1,700;1,800&display=swap" rel="stylesheet"></head>
<body style="margin:0;background:{GROUND}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{GROUND}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:{PANEL};border:1px solid {LINE};border-radius:4px;font:16px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:{INK}">
<tr><td style="padding:0;background:{t1};border-radius:3px 3px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td height="80" style="padding:0 18px;vertical-align:middle;height:80px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="padding-right:12px;vertical-align:middle"><a href="{link}"><img src="{SITE}/icon-180.png" width="44" height="44" alt="CFB Sundays" style="display:block;border:0;border-radius:4px"></a></td>
<td style="vertical-align:middle;{DISPLAY};font-size:30px;color:{tink}">CFB Sundays</td></tr></table></td>
<td width="64" height="80" style="width:64px;height:80px;padding:0;background:{t2};vertical-align:top;border-radius:0 3px 0 0"><div style="width:0;height:0;border-top:80px solid {t1};border-right:26px solid {t2};font-size:0;line-height:0"></div></td>
</tr></table></td></tr>
<tr><td style="height:4px;line-height:4px;font-size:0;background:{GOLD}">&nbsp;</td></tr>
<tr><td style="padding:12px 24px 4px"><div style="{LABEL};font-size:14px;color:{INK}">{e(self.label)} &middot; {self.season} season</div>
<div style="color:{MUTED};font-size:14px">This email is also <a href="{link}" style="color:#1546b8">a website</a>.</div></td></tr>
<tr><td style="padding:0 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{''.join(b[0] for b in blocks)}</table></td></tr>
<tr><td style="padding:20px 24px"><a href="{link}" style="display:inline-block;background:{GOLD};color:{GOLD_INK};text-decoration:none;{DISPLAY};font-size:17px;padding:10px 20px;border-radius:2px;border-bottom:2px solid #c99700">Every game and player &#9656;</a></td></tr>
<tr><td style="padding:0 24px 24px;color:{MUTED};font-size:12px">You signed up for this at cfbsundays.com. To change schools, sign up again there with the same address.
Teams are where each player was that week; a start means he was in the lineup for the first snap.<br>
<a href="{unsub_url}" style="color:{MUTED}">Unsubscribe</a></td></tr>
</table></td></tr></table></body></html>"""
        text = (f"CFB SUNDAYS: {self.label}, {self.season} season\nThis email is also a website: {link}\n" + "\n".join(b[1] for b in blocks) +
                f"\n\nEvery game and player: {link}\n\nUnsubscribe: {unsub_url}\n")
        return subject, html_doc, text

def send_batch(msgs):
    key = os.environ["RESEND_API_KEY"]
    for i in range(0, len(msgs), 100):
        http("https://api.resend.com/emails/batch", msgs[i:i + 100], {"Authorization": f"Bearer {key}"})

def main():
    wk = Week()
    if MODE == "preview":
        out = os.environ.get("PREVIEW_OUT", ".")
        schools = [s.strip() for s in os.environ.get("PREVIEW_SCHOOLS", "Georgia").split(",")]
        subject, h, t = wk.email(schools, "https://example.invalid/unsubscribe")
        open(os.path.join(out, "preview.html"), "w").write(h)
        open(os.path.join(out, "preview.txt"), "w").write(subject + "\n\n" + t)
        print("preview:", subject)
        return
    if wk.week is None:
        print("no finished week yet; nothing to send")
        return
    now = datetime.datetime.now(ZoneInfo("America/New_York"))
    # GitHub often starts scheduled runs late, so any run from 7 AM on counts;
    # the sends table below keeps the second Tuesday run from sending again.
    if MODE == "send" and now.hour < 7 and os.environ.get("FORCE") != "1":
        print(f"before 7 AM in New York ({now:%H:%M}); skipping")
        return
    acct, worker_url = worker_conf()
    if "__" in acct or "__" in worker_url:
        print("email signup isn't set up yet (worker/wrangler.toml, worker/URL); nothing to send")
        return
    db = D1(acct)
    if MODE == "send" and db.q("SELECT 1 FROM sends WHERE season = ? AND week = ?", (wk.season, wk.week)):
        print(f"{wk.label} {wk.season} already sent; nothing to do")
        return
    subs = db.q("SELECT norm, email, schools, unsub_token FROM subscribers WHERE status = 'active'")
    if MODE == "sample" and len(subs) > 3:
        sys.exit(f"sample mode refuses with {len(subs)} subscribers; use it only while testing")
    if len(subs) > RESEND_DAILY_FREE - 5:
        print(f"WARNING: {len(subs)} subscribers is past Resend's free 100-a-day limit; upgrade or switch providers")
    msgs = []
    for s in subs:
        unsub = f"{worker_url}/unsubscribe?t={s['unsub_token']}"
        subject, h, t = wk.email(json.loads(s["schools"]), unsub)
        msgs.append({"from": FROM, "to": [s["email"]], "reply_to": REPLY_TO, "subject": subject, "html": h, "text": t,
                     "headers": {"List-Unsubscribe": f"<{unsub}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}})
    if msgs:
        send_batch(msgs)
    if MODE == "send":
        t = int(now.timestamp())
        db.q("INSERT INTO sends (season, week, sent_at, count) VALUES (?, ?, ?, ?)", (wk.season, wk.week, t, len(msgs)))
        db.q("UPDATE subscribers SET last_sent_at = ? WHERE status = 'active'", (t,))
    print(f"sent {wk.label} ({wk.season}) to {len(msgs)} subscriber(s)")

if __name__ == "__main__":
    main()
