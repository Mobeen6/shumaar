// Question log, feedback and a private stats page for Shumaar's Ask (Cloudflare D1, binding DB).
// Stores only the question text, how it was answered and optional feedback: no IP address or other personal data.
let READY = false;
async function ready(db) {
  if (READY) return;
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS q (ts INTEGER, day TEXT, q TEXT, kind TEXT, match TEXT, conf REAL)"),
    db.prepare("CREATE TABLE IF NOT EXISTS fb (ts INTEGER, day TEXT, q TEXT, vote TEXT, note TEXT, kind TEXT)"),
    db.prepare("CREATE INDEX IF NOT EXISTS q_day ON q(day)"),
    db.prepare("CREATE INDEX IF NOT EXISTS fb_day ON fb(day)"),
  ]);
  READY = true;
}
const KINDS = new Set(["quick", "none", "munshi", "munshi_saved", "munshi_error"]);
const clip = (s, n) => String(s == null ? "" : s).replace(/\s+/g, " ").trim().slice(0, n);
const day = () => new Date().toISOString().slice(0, 10);

export async function logQuestion(db, o) {
  if (!db) return;
  const q = clip(o.q, 300), kind = KINDS.has(o.kind) ? o.kind : "quick";
  if (!q) return;
  await ready(db);
  await db.prepare("INSERT INTO q VALUES (?,?,?,?,?,?)").bind(Date.now(), day(), q, kind, clip(o.match, 60), +o.conf || null).run();
}
export async function logFeedback(db, o) {
  if (!db) return;
  const vote = o.vote === "up" ? "up" : o.vote === "down" ? "down" : "note";
  const q = clip(o.q, 300), note = clip(o.note, 600);
  if (!q && !note) return;
  await ready(db);
  await db.prepare("INSERT INTO fb VALUES (?,?,?,?,?,?)").bind(Date.now(), day(), q, vote, note, clip(o.kind, 20)).run();
}

const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const LAB = { quick: "Quick answer", none: "No match", munshi: "Munshi", munshi_saved: "Munshi (saved)", munshi_error: "Munshi failed" };

export async function statsPage(db, days) {
  await ready(db);
  const since = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
  const all = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results || [];
  const [byDay, byKind, top, none, votes, notes, munshi] = await Promise.all([
    all("SELECT day, kind, COUNT(*) n FROM q WHERE day>=? GROUP BY day, kind ORDER BY day DESC", since),
    all("SELECT kind, COUNT(*) n FROM q WHERE day>=? GROUP BY kind ORDER BY n DESC", since),
    all("SELECT LOWER(q) q, COUNT(*) n, MAX(day) last FROM q WHERE day>=? AND kind IN ('quick','none') GROUP BY LOWER(q) ORDER BY n DESC, last DESC LIMIT 60", since),
    all("SELECT LOWER(q) q, COUNT(*) n, MAX(day) last FROM q WHERE day>=? AND kind='none' GROUP BY LOWER(q) ORDER BY n DESC, last DESC LIMIT 60", since),
    all("SELECT vote, COUNT(*) n FROM fb WHERE day>=? AND vote IN ('up','down') GROUP BY vote", since),
    all("SELECT day, q, vote, note, kind FROM fb WHERE day>=? AND (note<>'' OR vote='down') ORDER BY ts DESC LIMIT 80", since),
    all("SELECT LOWER(q) q, COUNT(*) n, MAX(day) last FROM q WHERE day>=? AND kind LIKE 'munshi%' GROUP BY LOWER(q) ORDER BY n DESC, last DESC LIMIT 40", since),
  ]);
  const total = byKind.reduce((s, r) => s + r.n, 0) - byKind.filter((r) => r.kind.startsWith("munshi")).reduce((s, r) => s + r.n, 0);
  const v = Object.fromEntries(votes.map((r) => [r.vote, r.n]));
  const up = v.up || 0, dn = v.down || 0;
  const days_ = [...new Set(byDay.map((r) => r.day))];
  const cell = (d, k) => (byDay.find((r) => r.day === d && r.kind === k) || {}).n || 0;
  const tbl = (rows, cols) => rows.length ? `<div class="tw"><table><tr>${cols.map((c) => `<th>${c[0]}</th>`).join("")}</tr>${rows.map((r) => `<tr>${cols.map((c) => `<td${c[2] ? ' class="n"' : ""}>${esc(c[1](r))}</td>`).join("")}</tr>`).join("")}</table></div>` : `<p class="m">Nothing yet.</p>`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Shumaar Ask stats</title>
<style>:root{--bg:#f6f7f5;--fg:#17201d;--m:#5f6b66;--l:#dfe3e0;--a:#1f6f5c;--card:#fff}@media(prefers-color-scheme:dark){:root{--bg:#121816;--fg:#e7ece9;--m:#98a59f;--l:#2a3430;--a:#5fc0a3;--card:#1a2220;color-scheme:dark}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 Poppins,system-ui,sans-serif;padding:24px max(16px,env(safe-area-inset-left,0px))}main{max-width:1000px;margin:auto;display:grid;gap:22px}
h1{font-size:22px;margin:0}h2{font-size:16px;margin:0 0 8px}.m{color:var(--m);margin:0}.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.t{background:var(--card);border:1px solid var(--l);border-radius:10px;padding:12px 14px}.t b{display:block;font-size:24px;color:var(--a)}section{background:var(--card);border:1px solid var(--l);border-radius:10px;padding:14px 16px;min-width:0}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--l);vertical-align:top}th{color:var(--m);font-weight:500}td.n{text-align:right;font-variant-numeric:tabular-nums}
nav a{color:var(--a);margin-right:12px}</style></head><body><main>
<div><h1>Ask: what people are asking</h1><p class="m">Last ${days} days · <nav style="display:inline">${[7, 30, 90, 365].map((d) => `<a href="?days=${d}">${d} days</a>`).join("")}</nav></p></div>
<div class="tiles"><div class="t"><b>${total}</b>questions asked</div><div class="t"><b>${total ? Math.round(((byKind.find((r) => r.kind === "none") || {}).n || 0) / total * 100) : 0}%</b>got no quick match</div>
<div class="t"><b>${byKind.filter((r) => r.kind.startsWith("munshi")).reduce((s, r) => s + r.n, 0)}</b>went to Munshi</div><div class="t"><b>${up + dn ? Math.round(up / (up + dn) * 100) + "%" : "–"}</b>found the answer useful (${up} yes, ${dn} no)</div></div>
<section><h2>No answer: data to add</h2><p class="m">Questions the quick answer couldn't match.</p>${tbl(none, [["Question", (r) => r.q], ["Times", (r) => r.n, 1], ["Last asked", (r) => r.last]])}</section>
<section><h2>Feedback</h2><p class="m">"Not useful" votes and notes, newest first.</p>${tbl(notes, [["Date", (r) => r.day], ["Question", (r) => r.q], ["Vote", (r) => r.vote === "down" ? "No" : r.vote === "up" ? "Yes" : ""], ["Note", (r) => r.note]])}</section>
<section><h2>Top questions</h2>${tbl(top, [["Question", (r) => r.q], ["Times", (r) => r.n, 1], ["Last asked", (r) => r.last]])}</section>
<section><h2>Sent to Munshi</h2>${tbl(munshi, [["Question", (r) => r.q], ["Times", (r) => r.n, 1], ["Last asked", (r) => r.last]])}</section>
<section><h2>By day</h2>${tbl(days_, [["Day", (d) => d], ...["quick", "none", "munshi", "munshi_saved"].map((k) => [LAB[k], (d) => cell(d, k), 1])])}</section>
</main></body></html>`;
}
