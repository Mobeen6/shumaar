// Fill Shumaar's answer cache before visitors arrive, and export the answers as faq.json.
//
//   PREWARM_TOKEN=... node prewarm.mjs https://your-site.example [faq-questions.txt]
//
// Each question is asked once (one Claude call if it is not cached yet; cached ones are free).
// The worker keeps answers until the data is rebuilt, so every visitor who asks the same thing,
// or rewords it with the same key words, gets the saved answer without a new call.
// The answers are also written to faq.json. Put that file next to index.html (and publish it
// with the artifact) so the page shows them without asking the server at all.
import fs from "node:fs";
import AskCore from "../functions/_lib/askcore.js";

const site = (process.argv[2] || "").replace(/\/$/, "");
const file = process.argv[3] || new URL("./faq-questions.txt", import.meta.url).pathname;
if (!site) { console.error("Usage: PREWARM_TOKEN=... node prewarm.mjs https://your-site.example [questions.txt]"); process.exit(1); }
const qs = fs.readFileSync(file, "utf8").split("\n").map((s) => s.trim()).filter((s) => s && !s.startsWith("#"));
const out = { built: null, answers: {} };
let fresh = 0, cached = 0, failed = 0;
const h = await fetch(site + "/api/health").then((r) => r.json()).catch(() => ({}));
out.built = h.data || null;
for (const q of qs) {
  const r = await fetch(site + "/api/ask", { method: "POST", headers: { "content-type": "application/json", "x-prewarm": process.env.PREWARM_TOKEN || "" }, body: JSON.stringify({ q }) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || !j.text) { failed++; console.log("✗", q, j.code || r.status); continue; }
  j.cached ? cached++ : fresh++;
  out.answers[AskCore.sig(q)] = j.text;
  console.log(j.cached ? "·" : "✓", q);
  await new Promise((res) => setTimeout(res, 400));
}
fs.writeFileSync("faq.json", JSON.stringify(out));
console.log(`\n${fresh} new answers, ${cached} already saved, ${failed} failed. Wrote faq.json (${Object.keys(out.answers).length} answers).`);
