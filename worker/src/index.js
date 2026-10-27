// CFB Sundays signup handler (Cloudflare Worker + D1).
//   POST /subscribe      {email, schools[], token}  -> sends a confirmation link
//   GET  /confirm?t=...                             -> activates the subscription
//   GET  /unsubscribe?t= -> page with a button; POST -> unsubscribes (also the
//        one-click List-Unsubscribe-Post that Gmail and others send)
// One subscription per person: addresses are normalized (case, +tags, Gmail dots).
// Signing up again with the same address updates the schools after a new
// confirmation. Responses never reveal whether an address is already subscribed.

const MAX_SCHOOLS = 4;
const CONFIRM_TTL = 48 * 3600;        // confirmation links expire after 48 hours
const IP_LIMIT_PER_HOUR = 5;          // signup attempts per IP address per hour
const CONFIRMS_PER_DAY = 3;           // confirmation emails per address per day

export function normalizeEmail(raw) {
  const email = String(raw || "").trim().toLowerCase();
  if (email.length > 254 || !/^[^\s@<>()",;:]+@[a-z0-9.-]+\.[a-z]{2,}$/.test(email)) return null;
  const at = email.lastIndexOf("@");
  let local = email.slice(0, at), domain = email.slice(at + 1);
  local = local.split("+")[0];                       // name+anything@ is the same inbox
  if (domain === "googlemail.com") domain = "gmail.com";
  if (domain === "gmail.com") local = local.replace(/\./g, "");   // Gmail ignores dots
  if (!local) return null;
  return { email, norm: `${local}@${domain}` };
}

let schoolCache = { at: 0, names: null };
async function schoolNames(env) {
  const now = Date.now();
  if (!schoolCache.names || now - schoolCache.at > 3600e3) {
    const r = await fetch(`${env.SITE}/data/schools.json`, { cf: { cacheTtl: 3600 } });
    const list = await r.json();
    schoolCache = { at: now, names: new Set(list.map((s) => s.name)) };
  }
  return schoolCache.names;
}

const nowSec = () => Math.floor(Date.now() / 1000);
function randomToken() {
  const b = new Uint8Array(24);
  crypto.getRandomValues(b);
  return [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
}
async function sha256(s) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, "0")).join("");
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function corsHeaders(req, env) {
  const origin = req.headers.get("Origin") || "";
  const allowed = (env.ORIGINS || "").split(",").map((s) => s.trim());
  return {
    "Access-Control-Allow-Origin": allowed.includes(origin) ? origin : allowed[0] || "",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}
const json = (obj, headers, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { ...headers, "Content-Type": "application/json" } });

function page(env, title, bodyHtml, status = 200) {
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} - CFB Sundays</title>
<meta name="robots" content="noindex">
<style>:root{--bg:#f6f5f1;--ink:#1b1b18;--muted:#6e6a60;--accent:#a3261e;--accent-ink:#fff;--line:#dedacf;--surface:#fff}
@media(prefers-color-scheme:dark){:root{--bg:#16150f;--ink:#ece9df;--muted:#a09a8a;--accent:#d9544a;--accent-ink:#1b0d0c;--line:#37352a;--surface:#201f17}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,sans-serif}
main{max-width:520px;margin:12vh auto;padding:0 16px}h1{font-size:26px;margin:0 0 10px}p{color:var(--muted)}
a{color:var(--accent)}button{font:inherit;font-weight:600;background:var(--accent);color:var(--accent-ink);border:0;border-radius:8px;padding:10px 20px;cursor:pointer}</style>
</head><body><main><h1>${esc(title)}</h1>${bodyHtml}<p><a href="${env.SITE}/">Back to CFB Sundays</a></p></main></body></html>`;
  return new Response(html, { status, headers: { "Content-Type": "text/html; charset=utf-8" } });
}

async function sendMail(env, { to, subject, html, text, headers }) {
  if (env.DEV_LOG_MAIL === "1") { console.log("MAIL " + JSON.stringify({ to, subject, text })); return; }   // local tests only
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${String(env.RESEND_API_KEY || "").trim()}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: env.FROM, to: [to], reply_to: env.REPLY_TO, subject, html, text, headers }),
  });
  if (!r.ok) throw new Error(`Resend ${r.status}: ${(await r.text()).slice(0, 300)}`);
}

async function verifyCaptcha(env, token, ip) {
  if (!token) return false;
  if (env.DEV_FAKE_CAPTCHA === "1") return token === "pass";   // local tests only (.dev.vars, never deployed)
  const fd = new FormData();
  fd.append("secret", String(env.TURNSTILE_SECRET || "").trim());
  fd.append("response", token);
  if (ip) fd.append("remoteip", ip);
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: fd });
  const v = await r.json();
  return v.success === true;
}

async function subscribe(req, env) {
  let body;
  try { body = await req.json(); } catch { return [400, { ok: false, msg: "Something went wrong. Reload the page and try again." }]; }
  const addr = normalizeEmail(body.email);
  if (!addr) return [400, { ok: false, msg: "That email address doesn't look right." }];
  const valid = await schoolNames(env);
  const schools = [...new Set((Array.isArray(body.schools) ? body.schools : []).map(String))].filter((s) => valid.has(s));
  if (!schools.length) return [400, { ok: false, msg: "Pick at least one school." }];
  if (schools.length > MAX_SCHOOLS) return [400, { ok: false, msg: `Pick up to ${MAX_SCHOOLS} schools.` }];

  const ip = req.headers.get("CF-Connecting-IP") || "";
  const ipHash = await sha256(ip + "|" + env.TURNSTILE_SECRET);
  const t = nowSec();
  const db = env.DB;
  await db.prepare("DELETE FROM attempts WHERE at < ?").bind(t - 86400).run();
  const recent = await db.prepare("SELECT COUNT(*) AS n FROM attempts WHERE ip_hash = ? AND at > ?").bind(ipHash, t - 3600).first();
  if (recent.n >= IP_LIMIT_PER_HOUR) return [429, { ok: false, msg: "Too many tries from here. Try again in an hour." }];
  await db.prepare("INSERT INTO attempts (ip_hash, at) VALUES (?, ?)").bind(ipHash, t).run();

  if (!(await verifyCaptcha(env, body.token, ip))) return [400, { ok: false, msg: "The robot check didn't go through. Try it again." }];

  const done = { ok: true, msg: "Almost done. Check your inbox for a confirmation link. It expires in 48 hours." };
  const row = await db.prepare("SELECT * FROM subscribers WHERE norm = ?").bind(addr.norm).first();
  const sentToday = row && row.confirm_sent_at && t - row.confirm_sent_at < 86400 ? row.confirms_today : 0;
  if (sentToday >= CONFIRMS_PER_DAY) return [200, done];   // quietly stop mail-bombing an inbox

  const confirmToken = randomToken();
  const schoolsJson = JSON.stringify(schools);
  const transfers = body.transfers === true ? 1 : 0;
  if (!row) {
    await db.prepare(`INSERT INTO subscribers (norm, email, schools, status, pending_email, pending_schools,
        confirm_token, confirm_sent_at, confirms_today, unsub_token, created_at)
        VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, 1, ?, ?)`)
      .bind(addr.norm, addr.email, schoolsJson, addr.email, schoolsJson, confirmToken, t, randomToken(), t).run();
  } else {
    await db.prepare(`UPDATE subscribers SET pending_email = ?, pending_schools = ?, confirm_token = ?,
        confirm_sent_at = ?, confirms_today = ? WHERE norm = ?`)
      .bind(addr.email, schoolsJson, confirmToken, t, sentToday + 1, addr.norm).run();
  }

  await db.prepare(`INSERT INTO prefs (norm, pending_transfers) VALUES (?, ?)
      ON CONFLICT(norm) DO UPDATE SET pending_transfers = excluded.pending_transfers`).bind(addr.norm, transfers).run();

  const link = `${new URL(req.url).origin}/confirm?t=${confirmToken}`;
  const list = schools.join(", ");
  await sendMail(env, {
    to: addr.email,
    subject: "Confirm your CFB Sundays email",
    text: `Confirm to get the CFB Sundays email on Tuesday mornings: how ${list} players did in the NFL that week.\n\n${link}\n\nThe link expires in 48 hours. If you didn't sign up, ignore this and nothing happens.`,
    html: `<div style="font:16px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:#1b1b18;max-width:520px">
<p style="font-size:20px;font-weight:600;margin:0 0 12px">Confirm your CFB Sundays email</p>
<p>Confirm and you'll get an email on Tuesday mornings with how former <b>${esc(list)}</b> players did in the NFL that week.</p>
<p><a href="${link}" style="display:inline-block;background:#a3261e;color:#fff;text-decoration:none;font-weight:600;padding:11px 22px;border-radius:8px">Confirm</a></p>
<p style="color:#6e6a60;font-size:14px">The link expires in 48 hours. If you didn't sign up, ignore this and nothing happens.</p></div>`,
  });
  return [200, done];
}

async function confirm(url, env) {
  const token = url.searchParams.get("t") || "";
  const row = token && (await env.DB.prepare("SELECT * FROM subscribers WHERE confirm_token = ?").bind(token).first());
  if (!row) return page(env, "That link has already been used", `<p>If you already confirmed, you're all set. Otherwise sign up again on the site.</p>`, 404);
  if (nowSec() - row.confirm_sent_at > CONFIRM_TTL) return page(env, "That link expired", `<p>Confirmation links last 48 hours. Sign up again on the site and use the new link.</p>`, 410);
  await env.DB.prepare(`UPDATE subscribers SET email = pending_email, schools = pending_schools, status = 'active',
      pending_email = NULL, pending_schools = NULL, confirm_token = NULL, confirmed_at = ? WHERE norm = ?`)
    .bind(nowSec(), row.norm).run();
  await env.DB.prepare(`UPDATE prefs SET transfers = COALESCE(pending_transfers, transfers), pending_transfers = NULL WHERE norm = ?`)
    .bind(row.norm).run();
  const schools = JSON.parse(row.pending_schools).map(esc).join(", ");
  return page(env, "You're in", `<p>The CFB Sundays email arrives Tuesday mornings during the NFL season, covering <b>${schools}</b>.</p>
<p>To change schools later, sign up again on the site with the same address.</p>`);
}

async function unsubscribe(req, url, env) {
  const token = url.searchParams.get("t") || "";
  const row = token && (await env.DB.prepare("SELECT norm, status FROM subscribers WHERE unsub_token = ?").bind(token).first());
  if (req.method === "POST") {
    if (row) await env.DB.prepare("UPDATE subscribers SET status = 'unsubscribed' WHERE norm = ?").bind(row.norm).run();
    const oneClick = (await req.text()).includes("List-Unsubscribe=One-Click");
    if (oneClick) return new Response("Unsubscribed", { status: 200 });
    return page(env, "You're unsubscribed", `<p>No more Tuesday emails. You can sign up again any time on the site.</p>`);
  }
  if (!row) return page(env, "Link not found", `<p>This unsubscribe link isn't valid. If you're still getting email, reply to one and we'll take you off.</p>`, 404);
  if (row.status === "unsubscribed") return page(env, "You're unsubscribed", `<p>No more Tuesday emails. You can sign up again any time on the site.</p>`);
  // a button, not an automatic unsubscribe: mail scanners open links on their own
  return page(env, "Unsubscribe from CFB Sundays?", `<p>You'll stop getting the Tuesday email.</p>
<form method="post"><button type="submit">Unsubscribe</button></form>`);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const cors = corsHeaders(req, env);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    try {
      if (url.pathname === "/subscribe" && req.method === "POST") {
        const [status, body] = await subscribe(req, env);
        return json(body, cors, status);
      }
      if (url.pathname === "/confirm") return await confirm(url, env);
      if (url.pathname === "/unsubscribe") return await unsubscribe(req, url, env);
      if (url.pathname === "/") return Response.redirect(env.SITE, 302);
    } catch (e) {
      console.error(e && e.stack || e);
      if (url.pathname === "/subscribe") return json({ ok: false, msg: "Something went wrong on our end. Try again in a minute." }, cors, 500);
      return page(env, "Something went wrong", `<p>Try the link again in a minute.</p>`, 500);
    }
    return new Response("Not found", { status: 404 });
  },
};
