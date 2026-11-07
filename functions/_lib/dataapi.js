// Shumaar data API: free, read-only JSON (or CSV) from the same data the site uses. No AI, no keys.
// Served at /api/v1/... on the Pages site, or /v1/... on a standalone Worker.
import AskCore from "./askcore.js";

const slug = (s) => String(s).toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const PROV = { punjab: "Punjab", sindh: "Sindh", kp: "KP", kpk: "KP", "khyber-pakhtunkhwa": "KP", balochistan: "Balochistan", ict: "ICT", islamabad: "ICT", gb: "GB", "gilgit-baltistan": "GB", ajk: "AJK", "azad-jammu-and-kashmir": "AJK", "azad-jammu-kashmir": "AJK" };
const provOf = (q) => (q ? PROV[slug(q)] || q : null);
const csvCell = (v) => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
const toCSV = (rows) => rows.map((r) => r.map(csvCell).join(",")).join("\n");

export function makeDataApi(B) {
  const D = B.dist.map((d, i) => ({ ...d, id: i, slug: slug(d.n) }));
  const shortProv = (p) => ({ "Khyber Pakhtunkhwa": "KP", "Gilgit-Baltistan": "GB", "Azad Jammu & Kashmir": "AJK", "Islamabad ICT": "ICT" }[p] || p);
  const findD = (q) => { const s = slug(q); return D.find((d) => d.slug === s) || (B.alias[s] ? D.find((d) => d.n === B.alias[s][0]) : null) || D.find((d) => d.slug.startsWith(s)); };
  const built = B.built;
  const meta = { source: "Shumaar (shumaar data API v1)", built, licence: "Free to use; cite Shumaar and the original source named in each record." };

  const routes = {
    "": () => ({ ...meta, endpoints: {
      "/indicators": "All province and national indicators. ?theme= to filter.",
      "/indicators/{id}": "One indicator: values by province, previous round, definition, source.",
      "/layers": "All district map layers. ?theme= to filter.",
      "/layers/{code}": "One layer for every district. ?province= to filter; ?format=csv.",
      "/districts": "All 160 districts. ?province= to filter.",
      "/districts/{name}": "Every layer for one district, e.g. /districts/rajanpur.",
      "/tables": "Chart data tables behind the site.",
      "/tables/{key}": "One table's rows; ?format=csv.",
      "/search?q=": "Find indicators, layers and tables by words.",
    } }),
    indicators: (p, q) => { const th = q.get("theme"); return { ...meta, count: 0, data: B.ind.filter((i) => !th || slug(i.theme) === slug(th)).map((i) => ({ id: i.id, name: i.name, theme: i.theme, unit: i.unit, level: i.lvl, source: i.src, district_layer: i.map })) }; },
    "indicators/:id": (p) => { const i = B.ind.find((x) => x.id === p.id); if (!i) return null; const { kw, ...rest } = i; return { ...meta, data: rest }; },
    layers: (p, q) => { const th = q.get("theme"); return { ...meta, data: Object.entries(B.layers).filter(([, l]) => !th || slug(l.theme) === slug(th)).map(([code, l]) => ({ code, label: l.label, theme: l.theme, unit: l.unit, rural_only: l.rural, higher_is_bad: l.hb })) }; },
    "layers/:code": (p, q) => { const l = B.layers[p.code]; if (!l) return null; const pv = provOf(q.get("province"));
      const rows = D.filter((d) => d.v[p.code] && (!pv || shortProv(d.p) === pv)).map((d) => ({ district: d.n, province: shortProv(d.p), value: d.v[p.code][0], n: d.v[p.code][1] === 99999 ? null : d.v[p.code][1] }));
      if (q.get("format") === "csv") return { csv: toCSV([["district", "province", "value", "unit", "observations", "source"], ...rows.map((r) => [r.district, r.province, r.value, l.unit, r.n, l.src])]), name: p.code };
      return { ...meta, layer: { code: p.code, ...l }, province_values: B.prov[p.code] || {}, count: rows.length, data: rows }; },
    districts: (p, q) => { const pv = provOf(q.get("province")); return { ...meta, data: D.filter((d) => !pv || shortProv(d.p) === pv).map((d) => ({ slug: d.slug, name: d.n, province: shortProv(d.p), division: d.dv || null, layers: Object.keys(d.v).length })) }; },
    "districts/:name": (p, q) => { const d = findD(p.name); if (!d) return null;
      const vals = Object.entries(d.v).map(([c, x]) => ({ code: c, label: (B.layers[c] || {}).label, value: x[0], unit: (B.layers[c] || {}).unit, observations: x[1] === 99999 ? null : x[1], source: (B.layers[c] || {}).src }));
      if (q.get("format") === "csv") return { csv: toCSV([["district", "province", "code", "label", "value", "unit", "observations", "source"], ...vals.map((v) => [d.n, shortProv(d.p), v.code, v.label, v.value, v.unit, v.observations, v.source])]), name: d.slug };
      return { ...meta, district: { name: d.n, province: shortProv(d.p), division: d.dv || null }, count: vals.length, data: vals }; },
    tables: () => ({ ...meta, data: Object.entries(B.tables).map(([k, t]) => ({ key: k, title: t.title, source: t.src, series: t.inds.length, periods: t.pers.length })) }),
    "tables/:key": (p, q) => { const t = B.tables[p.key]; if (!t) return null; const head = ["indicator", "area", "period", "value"]; if (t.units.length > 1) head.push("unit");
      if (q.get("format") === "csv") return { csv: toCSV([head, ...t.rows]), name: p.key };
      return { ...meta, table: { key: p.key, title: t.title, source: t.src, units: t.units }, columns: head, data: t.rows }; },
    search: (p, q) => { const s = (q.get("q") || "").trim(); if (!s) return { ...meta, data: [] }; return { ...meta, query: s, data: AskCore.search(B, s, 15) }; },
  };

  return function handle(path, query) {
    const parts = path.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean);
    let key = parts.join("/"), params = {};
    if (parts.length === 2) { const pat = parts[0] + "/:" + { indicators: "id", layers: "code", districts: "name", tables: "key" }[parts[0]]; if (routes[pat]) { key = pat; params = { [pat.split(":")[1]]: decodeURIComponent(parts[1]) }; } }
    const fn = routes[key]; if (!fn) return { status: 404, body: { error: "not_found", hint: "See /api/v1 for the list of endpoints." } };
    const out = fn(params, query); if (!out) return { status: 404, body: { error: "not_found" } };
    if (out.data && "count" in out) out.count = out.data.length;
    return { status: 200, body: out };
  };
}
