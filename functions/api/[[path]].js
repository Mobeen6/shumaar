// Cloudflare Pages Function: serves /api/ask and /api/health with the same code as the standalone Worker.
import worker from "../_lib/worker.js";
export const onRequest = (ctx) => worker.fetch(ctx.request, ctx.env, { waitUntil: (p) => ctx.waitUntil(p) });
