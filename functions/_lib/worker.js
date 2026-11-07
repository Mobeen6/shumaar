// Shumaar Ask: a small Cloudflare Worker that answers free-text questions with Claude,
// using only Shumaar's own data. Three cost controls are built in:
//   1. Claude Haiku (cheapest model), short answers, at most 4 tool rounds.
//   2. Answers saved in KV under a word-signature key ("literacy in Lahore?" = "lahore literacy"),
//      tied to the data version, so repeat and reworded questions cost nothing. They are kept until
//      the data is rebuilt (CACHE_TTL=0) or for CACHE_TTL seconds.
//   3. Prompt caching: the instructions + data catalog (~7k tokens) are cached by
//      Anthropic and billed at a tenth of the normal input price on reuse.
// Plus limits: PER_IP_DAY questions per visitor per day and DAILY_CAP questions in total.
import AskCore from "./askcore.js";
import BUNDLE from "./askdata.json";
import { makeDataApi } from "./dataapi.js";
const DATA = makeDataApi(BUNDLE);

const CATALOG = AskCore.catalog(BUNDLE);
const TOOLS = AskCore.tools(BUNDLE);
const API_TOOLS = TOOLS.map((t) => ({ name: t.name, description: t.description, input_schema: t.inputSchema }));
const SYSTEM = [
  { type: "text", text: AskCore.RULES },
  // Breakpoint here caches tools + rules + catalog together for an hour.
  { type: "text", text: "Data catalog (ids you can pass to the tools):\n" + CATALOG, cache_control: { type: "ephemeral", ttl: "1h" } },
];

const json = (body, status, cors) => new Response(JSON.stringify(body), { status: status || 200, headers: { "content-type": "application/json; charset=utf-8", ...cors } });
const normQ = (q) => AskCore.norm(q).replace(/\s+/g, " ").trim();
const VER = String(BUNDLE.built || "v").replace(/[^0-9a-z]/gi, "").slice(0, 16);
const cacheKey = (q) => "a2:" + VER + ":" + (AskCore.sig(q) || normQ(q));
const today = () => new Date().toISOString().slice(0, 10);

async function bump(kv, key, limit) {
  // KV is eventually consistent, so this is a soft limit (good enough to stop runaway costs).
  const n = +(await kv.get(key)) || 0;
  if (n >= limit) return false;
  await kv.put(key, String(n + 1), { expirationTtl: 60 * 60 * 26 });
  return true;
}

async function callClaude(env, messages, final) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({
      model: env.MODEL || "claude-haiku-5-5",
      max_tokens: +(env.MAX_TOKENS || 500),
      system: SYSTEM,
      tools: API_TOOLS,
      messages,
      ...(final ? { tool_choice: { type: "none" } } : {}),
      cache_control: { type: "ephemeral" }, // automatic caching of the growing tool conversation
    }),
  });
  if (!r.ok) throw Object.assign(new Error("anthropic " + r.status + " " + (await r.text()).slice(0, 300)), { code: r.status === 429 ? "rate_limited" : "upstream_error" });
  return r.json();
}

async function answer(env, q) {
  const messages = [{ role: "user", content: "Question: " + q }];
  const usage = { in: 0, out: 0, cache_read: 0, cache_write: 0 };
  for (let round = 0; round < 5; round++) {
    const res = await callClaude(env, messages, round === 4);
    const u = res.usage || {};
    usage.in += u.input_tokens || 0; usage.out += u.output_tokens || 0;
    usage.cache_read += u.cache_read_input_tokens || 0; usage.cache_write += u.cache_creation_input_tokens || 0;
    const uses = (res.content || []).filter((c) => c.type === "tool_use");
    if (res.stop_reason !== "tool_use" || !uses.length || round === 4) {
      const text = (res.content || []).filter((c) => c.type === "text").map((c) => c.text).join("\n").trim();
      return { text, usage };
    }
    messages.push({ role: "assistant", content: res.content });
    const results = uses.map((tu) => {
        const t = TOOLS.find((x) => x.name === tu.name);
        let out, isErr = false;
        try { out = t ? t.run(tu.input || {}) : "Unknown tool"; } catch (e) { out = "Error: " + e.message; isErr = true; }
        return { type: "tool_result", tool_use_id: tu.id, content: typeof out === "string" ? out : JSON.stringify(out), ...(isErr ? { is_error: true } : {}) };
      });
    if (round === 3) results.push({ type: "text", text: "Answer now with what you have." });
    messages.push({ role: "user", content: results });
  }
}

export default {
  async fetch(req, env, ctx) {
    const origin = req.headers.get("origin") || "";
    const allowed = (env.ALLOWED_ORIGIN || "*").split(",").map((s) => s.trim());
    const cors = {
      "access-control-allow-origin": allowed.includes("*") ? "*" : allowed.includes(origin) ? origin : allowed[0],
      "access-control-allow-methods": "POST, OPTIONS",
      "access-control-allow-headers": "content-type, x-prewarm",
      vary: "origin",
    };
    const url = new URL(req.url);
    // Public data API: GET /api/v1/... (Pages) or /v1/... (Worker). Open to every origin, cached at the edge.
    const m = url.pathname.match(/\/v1(\/.*)?$/);
    if (m) {
      const open = { "access-control-allow-origin": "*", "access-control-allow-methods": "GET, OPTIONS", "access-control-allow-headers": "content-type" };
      if (req.method === "OPTIONS") return new Response(null, { headers: open });
      if (req.method !== "GET") return json({ error: "method_not_allowed" }, 405, open);
      const r = DATA(m[1] || "", url.searchParams);
      const head = { ...open, "cache-control": "public, max-age=3600" };
      if (r.body && r.body.csv != null) return new Response(r.body.csv, { status: 200, headers: { ...head, "content-type": "text/csv; charset=utf-8", "content-disposition": `attachment; filename="shumaar-${r.body.name}.csv"` } });
      return json(r.body, r.status, head);
    }
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (url.pathname.endsWith("/health")) return json({ ok: !!(env.ANTHROPIC_API_KEY && env.ASK_KV), data: BUNDLE.built }, 200, cors);
    if (url.pathname.endsWith("/sig")) return json({ sig: AskCore.sig(url.searchParams.get("q") || "") }, 200, cors);
    if (req.method !== "POST" || !url.pathname.endsWith("/ask")) return json({ code: "not_found" }, 404, cors);

    let q = "";
    try { q = String((await req.json()).q || "").trim(); } catch (e) {}
    if (!q || q.length > 300) return json({ code: "bad_question" }, 400, cors);

    // 1. Saved answer?
    const key = cacheKey(q);
    const hit = await env.ASK_KV.get(key);
    if (hit) return json({ text: hit, cached: true }, 200, cors);

    // 2. Limits (only questions that reach Claude count).
    const ip = req.headers.get("cf-connecting-ip") || "anon";
    const prewarm = env.PREWARM_TOKEN && req.headers.get("x-prewarm") === env.PREWARM_TOKEN; // lets prewarm.mjs fill the cache past the per-visitor limit
    if (!prewarm && !(await bump(env.ASK_KV, `r:${today()}:${ip}`, +(env.PER_IP_DAY || 20)))) return json({ code: "daily_limit" }, 429, cors);
    if (!(await bump(env.ASK_KV, `g:${today()}`, +(env.DAILY_CAP || 1000)))) return json({ code: "daily_limit" }, 429, cors);

    // 3. Ask Claude.
    try {
      const { text, usage } = await answer(env, q);
      if (!text) return json({ code: "empty_completion" }, 502, cors);
      const ttl = +(env.CACHE_TTL ?? 0);
      ctx.waitUntil(env.ASK_KV.put(key, text, ttl >= 60 ? { expirationTtl: ttl } : {}));
      console.log(JSON.stringify({ q: normQ(q), key, usage }));
      return json({ text, cached: false }, 200, cors);
    } catch (e) {
      console.log("error", e.message);
      return json({ code: e.code || "upstream_error" }, 502, cors);
    }
  },
};
