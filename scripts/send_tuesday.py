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
CATS = [  # label, sort value, tiebreak, did he do it at all, line
    ("Passing", lambda w: w.get("py", 0), lambda w: w.get("ptd", 0), lambda w: w.get("att", 0) > 0,
     lambda w: f"{w.get('cmp',0)}/{w.get('att',0)}, {w.get('py',0)} yds, {w.get('ptd',0)} TD" + (f", {w['int']} INT" if w.get("int") else "")),
    ("Rushing", lambda w: w.get("ry", 0), lambda w: w.get("rtd", 0), lambda w: w.get("car", 0) > 0,
     lambda w: f"{w.get('car',0)} car, {w.get('ry',0)} yds" + (f", {w['rtd']} TD" if w.get("rtd") else "")),
    ("Receiving", lambda w: w.get("recy", 0), lambda w: w.get("rectd", 0), lambda w: w.get("rec", 0) > 0,
     lambda w: f"{w.get('rec',0)} rec, {w.get('recy',0)} yds" + (f", {w['rectd']} TD" if w.get("rectd") else "")),
    ("Sacks", lambda w: w.get("sk", 0), lambda w: tk(w), lambda w: w.get("sk", 0) > 0,
     lambda w: f"{fmt(w['sk'])} sack{'s' if w['sk'] != 1 else ''}"),
    ("Tackles", lambda w: tk(w), lambda w: w.get("sk", 0), lambda w: tk(w) > 0,
     lambda w: f"{tk(w)} tackle{'s' if tk(w) != 1 else ''}"),
    ("Interceptions", lambda w: w.get("dint", 0), lambda w: w.get("pd", 0), lambda w: w.get("dint", 0) > 0,
     lambda w: f"{w['dint']} INT" + (f", {w['pd']} PD" if w.get("pd") else "")),
]
POS_ORDER = {p: i for i, p in enumerate(["QB", "RB", "FB", "WR", "TE", "OL", "T", "G", "C", "DL", "DE", "DT", "NT",
                                         "LB", "OLB", "ILB", "MLB", "DB", "CB", "S", "FS", "SS", "K", "P", "LS"])}
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
        teams (so Monday night is in before anything goes out)."""
        weeks = sorted({g["wk"] for g in self.games})
        done = []
        for w in weeks:
            gs = [g for g in self.games if g["wk"] == w]
            if not gs or any(g["as"] == "" for g in gs):
                continue
            teams = {team_for(self.players[pid], w, None) for pid, l in self.lines.items()
                     if w in l and pid in self.players}
            if all(g["away"] in teams and g["home"] in teams for g in gs):
                done.append(w)
        return done[-1] if done else None

    def school_block(self, sc):
        mine = [(pid, p) for pid, p in self.players.items() if p["c"] and p["c"][0] == sc]
        rows = [(pid, p, self.lines[pid][self.week]) for pid, p in mine
                if self.week in self.lines.get(pid, {})]
        col = (self.colors.get("school", {}).get(sc) or ["#a3261e"])[0]
        sums = {k: sum(r[2].get(k, 0) for r in rows) for k in ("py", "ry", "recy", "ptd", "rtd", "rectd", "sk", "dint")}
        tds = sums["ptd"] + sums["rtd"] + sums["rectd"]
        parts = [(sums["py"], f"{sums['py']:,} pass yds"), (sums["ry"], f"{sums['ry']:,} rush yds"),
                 (sums["recy"], f"{sums['recy']:,} rec yds"), (tds, f"{tds} TD{'s' if tds != 1 else ''}"),
                 (sums["sk"], f"{fmt(sums['sk'])} sack{'s' if sums['sk'] != 1 else ''}"),
                 (sums["dint"], f"{sums['dint']} INT{'s' if sums['dint'] != 1 else ''}")]
        totals = " · ".join(t for v, t in parts if v)
        mute = "color:#6e6a60;font-size:13px"
        h = [f'<tr><td style="padding:22px 0 4px;border-top:1px solid #dedacf">'
             f'<div style="font-size:20px;font-weight:700;text-transform:uppercase;letter-spacing:.4px">'
             f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{col};margin-right:8px"></span>{e(sc)}</div>']
        t = [f"\n{sc.upper()}"]
        wk = self.week
        on_field = [(pid, p) for pid, p in mine
                    if wk in p.get("pw", []) or wk in p.get("gs", []) or wk in self.lines.get(pid, {})]
        if not on_field:
            h.append('<p style="color:#6e6a60;margin:6px 0 0">No former players saw the field this week.</p></td></tr>')
            t.append("No former players saw the field this week.")
            return "".join(h), "\n".join(t)
        if totals:
            h.append(f'<p style="color:#6e6a60;font-size:14px;margin:4px 0 12px">{totals}</p>')
            t.append(totals)
        # everyone with a number in each of the six categories, best first
        for lbl, val, tb, did, line in CATS:
            cand = sorted((r for r in rows if did(r[2])), key=lambda r: (-val(r[2]), -tb(r[2]), r[1]["n"]))
            if not cand:
                continue
            h.append(f'<p style="margin:10px 0 2px;{mute};text-transform:uppercase;letter-spacing:.5px">{lbl}</p>')
            t.append(f"\n{lbl}")
            for pid, p, w in cand:
                team = team_for(p, wk, None)
                h.append(f'<p style="margin:0 0 3px"><b>{e(p["n"])}</b> <span style="{mute}">{team}</span> {e(line(w))}</p>')
                t.append(f"  {p['n']} ({team}) {line(w)}")
        def roster(group):
            group = sorted(group, key=lambda x: (POS_ORDER.get(x[1]["p"], 99), x[1]["n"]))
            return ", ".join(f"{p['p']} {p['n']} ({team_for(p, wk, None)})" for _, p in group)
        started = [(pid, p) for pid, p in on_field if wk in p.get("gs", [])]
        others = [(pid, p) for pid, p in on_field if wk not in p.get("gs", [])]
        for lbl, group in (("Started", started), ("Also played", others)):
            if group:
                h.append(f'<p style="margin:14px 0 0;font-size:14px"><span style="{mute};text-transform:uppercase;letter-spacing:.5px">'
                         f'{lbl} ({len(group)})</span><br>{e(roster(group))}</p>')
                t.append(f"\n{lbl} ({len(group)}): {roster(group)}")
        h.append("</td></tr>")
        return "".join(h), "\n".join(t)

    def email(self, schools, unsub_url):
        blocks = [self.school_block(sc) for sc in schools]
        link = f"{SITE}/?s=" + ",".join(urllib.request.quote(s) for s in schools)
        who = schools[0] if len(schools) == 1 else ", ".join(schools[:-1]) + " and " + schools[-1]
        subject = f"{self.label}: how your {who} guys did"
        html_doc = f"""<!doctype html><html><body style="margin:0;background:#f6f5f1">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f5f1"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border:1px solid #dedacf;border-radius:12px;font:16px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1b1b18">
<tr><td style="padding:24px 24px 8px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="padding-right:12px;vertical-align:middle"><a href="{link}"><img src="{SITE}/icon-180.png" width="44" height="44" alt="CFB Sundays" style="display:block;border:0;border-radius:8px"></a></td>
<td style="vertical-align:middle"><div style="font-size:24px;font-weight:800;letter-spacing:.5px">CFB SUNDAYS</div></td></tr></table>
<div style="color:#6e6a60;font-size:14px;padding-top:8px">This email is also <a href="{link}" style="color:#a3261e">a website</a>. {e(self.label)}, {self.season} season.</div></td></tr>
<tr><td style="padding:0 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{''.join(b[0] for b in blocks)}</table></td></tr>
<tr><td style="padding:20px 24px"><a href="{link}" style="display:inline-block;background:#a3261e;color:#ffffff;text-decoration:none;font-weight:600;padding:10px 20px;border-radius:8px">Every game and player on CFB Sundays</a></td></tr>
<tr><td style="padding:0 24px 24px;color:#6e6a60;font-size:12px">You signed up for this at cfbsundays.com. To change schools, sign up again there with the same address.
Teams are where each player was that week; a start means he was in the lineup for the first snap.<br>
<a href="{unsub_url}" style="color:#6e6a60">Unsubscribe</a></td></tr>
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
