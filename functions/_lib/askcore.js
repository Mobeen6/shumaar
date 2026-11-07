/* AskCore: Claude's tools over Shumaar's data. Shared by the page (claude.ai) and the Cloudflare Worker (own site). */
const AskCore=(()=>{
const STOP=new Set("a an the of in on for to and or is are was were be by at as with from what whats how many much does do did which who where when why show me tell about give data rate share percent percentage level number total pakistan its it this that there their people per my our can could would should please like get value figure stat stats latest current now today ki ka ke kya hai mein".split(" "));
const strip=s=>String(s==null?"":s).replace(/<[^>]+>/g,"").replace(/&nbsp;/g," ").replace(/&amp;/g,"&").replace(/\s+/g," ").trim();
const norm=s=>String(s).toLowerCase().replace(/[’']/g,"").replace(/[^a-z0-9.]+/g," ").trim();
const stem=w=>w.length>4&&w.endsWith("ies")?w.slice(0,-3)+"y":w.length>3&&w.endsWith("s")&&!w.endsWith("ss")?w.slice(0,-1):w;
const toks=s=>norm(s).split(" ").filter(w=>w&&!STOP.has(w)).map(stem);
// Cache key: the question's meaningful words, canonical spellings, sorted. "Literacy rate in Lahore?" and "lahore literacy" share one key.
const CANON={kpk:"kp",khyber:"kp",pakhtunkhwa:"kp",baluchistan:"balochistan",enrollment:"enrolment",immunization:"immunisation",vaccination:"immunisation",vaccine:"immunisation",labor:"labour",vs:"",versus:"",compare:"",compared:"",comparison:"",between:"",against:"",highest:"most",largest:"most",biggest:"most",top:"most",lowest:"least",smallest:"least",fewest:"least",kid:"child",children:"child",childrens:"child",fy:"",year:"",rs:"",rupee:"rupee",dollar:"usd"};
const sig=s=>[...new Set(toks(s).map(w=>CANON[w]!==undefined?CANON[w]:w).filter(Boolean))].sort().join(" ");
function lev(a,b,max){ if(Math.abs(a.length-b.length)>max) return max+1; let p=Array.from({length:b.length+1},(_,j)=>j);
  for(let i=1;i<=a.length;i++){ const c=[i]; let mn=i; for(let j=1;j<=b.length;j++){ c[j]=Math.min(p[j]+1,c[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1)); if(c[j]<mn) mn=c[j]; } if(mn>max) return max+1; p=c; } return p[b.length]; }
const r2=x=>x==null||typeof x!=="number"?x:Math.abs(x)>=100?Math.round(x):Math.round(x*100)/100;

/* ---- bundle: everything Claude may read, as plain data ---- */
function makeBundle(src){ try{ applyKWX(); }catch(e){}
  const {IND,D,GEO,REG,P,PROVKEY,DALIAS}=src;
  const ind=IND.map(i=>{ const g=i.g||P; return {id:i.id,theme:i.theme,name:i.name,unit:i.unit||"",
    values:g.map((n,k)=>[n,r2(i.v[k])]).filter(x=>x[1]!=null),
    prev:i.prev?{when:i.prev.w,values:g.map((n,k)=>[n,r2(i.prev.v[k])]).filter(x=>x[1]!=null)}:null,
    hb:i.hb==null?null:!!i.hb,src:strip(i.src),def:strip(i.def),lvl:strip(i.lvl),cav:strip(i.cav),map:i.map||null,kw:(i.kw||[]).slice(0,14)}; });
  const layers={}; for(const [c,i] of Object.entries(D.inds)) layers[c]={label:i.label,theme:i.theme||"",unit:i.unit||"",src:strip(i.orig||i.src),hb:i.hb==null?null:!!i.hb,rural:!!i.rural,noN:!!i.noN};
  const dist=GEO.features.map(f=>{ const v=D.vals[f.id]||{}; const o={}; for(const c in v){ const x=v[c]; if(x&&x[0]!=null) o[c]=[r2(x[0]),x[1]]; } return {n:f.properties.n,p:PROVKEY[f.properties.p]||f.properties.p,dv:f.properties.dv||"",v:o}; });
  const prov={}; for(const c in D.prov){ prov[c]={}; for(const k in D.prov[c]) prov[c][PROVKEY[k]||k]=r2(D.prov[c][k]); }
  const tables={};
  for(const k of Object.keys(REG)){ let rows; try{ rows=REG[k](); }catch(e){ continue; } if(!rows||!rows.length) continue;
    const ds=[...new Set(rows.map(r=>r[0]))], srcs=[...new Set(rows.map(r=>r[6]).filter(Boolean))], units=[...new Set(rows.map(r=>r[5]).filter(Boolean))];
    const sig=ds.join("|")+rows.length; if(Object.values(tables).some(t=>t.sig===sig)) continue;
    tables[k]={sig,title:ds.slice(0,3).join("; "),src:srcs.slice(0,3).join("; "),units:units.slice(0,6),
      inds:[...new Set(rows.map(r=>String(r[1])))],geos:[...new Set(rows.map(r=>String(r[2])))],pers:[...new Set(rows.map(r=>String(r[3])))],
      rows:rows.map(r=>{ const o=[String(r[1]),String(r[2]),String(r[3]),r2(+r[4])]; if(units.length>1) o.push(r[5]); if(r[8]) o.push("note: "+r[8]); return o; })}; }
  for(const k in tables) delete tables[k].sig;
  return {v:1,built:new Date().toISOString().slice(0,10),ind,layers,dist,prov,tables,alias:DALIAS||{}};
}

/* ---- catalog: a compact list of everything, for the prompt ---- */
function catalog(B){
  const L=[];
  L.push("INDICATORS (id | name | unit):"); B.ind.forEach(i=>L.push(`${i.id} | ${i.name} | ${i.unit}`));
  L.push("\nDISTRICT LAYERS (code | label | unit):"); Object.entries(B.layers).forEach(([c,l])=>L.push(`${c} | ${l.label}${l.rural?" (rural)":""} | ${l.unit}`));
  L.push("\nTABLES (key | title | sample series):"); Object.entries(B.tables).forEach(([k,t])=>L.push(`${k} | ${t.title} | ${t.inds.slice(0,6).join(", ")}${t.inds.length>6?", …":""} | ${t.pers.length>1?t.pers[0]+"–"+t.pers.at(-1):t.pers[0]||""}`));
  L.push(`\n${B.dist.length} districts are covered.`);
  return L.join("\n"); }

/* ---- search ---- */
function score(qt,text){ const tt=toks(text); if(!tt.length) return 0; let h=0;
  for(const w of qt){ let m=0; for(const v of tt){ const x=w===v?1:(w.length>=4&&v.length>=4&&(v.startsWith(w)||w.startsWith(v)))?.7:(w.length>=5&&lev(w,v,1)<=1)?.6:0; if(x>m) m=x; if(m===1) break; } h+=m; }
  return h/qt.length + .15*Math.min(1,h/tt.length); }
function search(B,q,limit){ const qt=toks(q); if(!qt.length) return []; const out=[];
  B.ind.forEach(i=>out.push({s:score(qt,i.name+" "+i.theme+" "+i.kw.join(" ")),type:"indicator",id:i.id,name:i.name,unit:i.unit}));
  Object.entries(B.layers).forEach(([c,l])=>out.push({s:score(qt,l.label+" "+l.theme)-.02,type:"district_layer",code:c,name:l.label,unit:l.unit}));
  Object.entries(B.tables).forEach(([k,t])=>out.push({s:score(qt,t.title+" "+t.inds.slice(0,40).join(" "))-.03,type:"table",key:k,name:t.title,series:t.inds.slice(0,8)}));
  return out.filter(o=>o.s>.3).sort((a,b)=>b.s-a.s).slice(0,limit||10).map(o=>{ delete o.s; return o; }); }

/* ---- districts ---- */
function findDistrict(B,name){ const q=norm(name).replace(/\b(district|city|tehsil)\b/g,"").trim(); if(!q) return null;
  const ex=B.dist.find(d=>norm(d.n)===q); if(ex) return {d:ex};
  for(const a in B.alias){ if(norm(a)===q){ const n=B.alias[a][0]; const d=B.dist.find(x=>x.n===n); if(d) return {d,note:`"${name}" covers ${B.alias[a].join(", ")}; showing ${n}.`}; } }
  let best=null; for(const d of B.dist){ const k=norm(d.n); const e=Math.min(lev(q,k,2),lev(q.replace(/ /g,""),k.replace(/ /g,""),2)); if(e<=2&&(!best||e<best.e)) best={e,d}; }
  if(best) return {d:best.d,note:best.e?`Matched "${name}" to ${best.d.n}.`:undefined};
  const sub=B.dist.find(d=>norm(d.n).includes(q)||q.includes(norm(d.n))); return sub?{d:sub}:null; }
function rankIn(B,code,d){ const L=B.layers[code]; const peers=B.dist.filter(x=>x.p===d.p&&x.v[code]&&(L.noN||x.v[code][1]>=25));
  const s=[...peers].sort((a,b)=>L.hb?a.v[code][0]-b.v[code][0]:b.v[code][0]-a.v[code][0]); const r=s.indexOf(d)+1; return r?`${r} of ${s.length} in ${d.p}${L.hb==null?" (ordered high to low)":L.hb?" (1 = lowest = best)":" (1 = highest = best)"}`:undefined; }
function districtRow(B,code,d){ const L=B.layers[code], x=d.v[code]; if(!x) return null;
  return {layer:code,label:L.label,value:x[0],unit:L.unit,sample:L.noN?undefined:x[1],reliability:L.noN?undefined:x[1]<25?"too few observations":x[1]<100?"small sample, indicative":"ok",
    province_value:(B.prov[code]||{})[d.p],pakistan_value:(B.prov[code]||{}).Pakistan,rank:rankIn(B,code,d),source:L.src}; }

/* ---- tools ---- */
function tools(B){ return [
 {name:"search",description:"Find which national indicators, district map layers and data tables match a topic. Returns ids/codes/keys to use with the other tools. Call this first unless the catalog already gives the id.",
  inputSchema:{type:"object",properties:{query:{type:"string",description:"topic words, e.g. 'wheat imports' or 'female literacy'"}},required:["query"]},
  run:({query})=>search(B,String(query||""),10)},
 {name:"get_indicator",description:"National (and where available provincial or group) values of one indicator, with previous survey round, source, definition and caveats.",
  inputSchema:{type:"object",properties:{id:{type:"string"}},required:["id"]},
  run:({id})=>{ const i=B.ind.find(x=>x.id===String(id)); if(!i) throw new Error("No indicator with id "+id+". Use search."); const o={...i}; delete o.kw; return o; }},
 {name:"get_district",description:"Values for one district (any of ~160). Give layer codes to get those layers with province and Pakistan values and the district's rank in its province; omit layers to get every available layer value.",
  inputSchema:{type:"object",properties:{district:{type:"string"},layers:{type:"array",items:{type:"string"}}},required:["district"]},
  run:({district,layers})=>{ const f=findDistrict(B,String(district||"")); if(!f) throw new Error("No district called "+district+".");
    const d=f.d; const codes=Array.isArray(layers)&&layers.length?layers.map(String):Object.keys(d.v);
    const rows=codes.map(c=>B.layers[c]?(Array.isArray(layers)&&layers.length?districtRow(B,c,d):(d.v[c]?[c,B.layers[c].label,d.v[c][0],B.layers[c].unit]:null)):null).filter(Boolean);
    return {district:d.n,province:d.p,division:d.dv||undefined,note:f.note,values:rows}; }},
 {name:"rank_districts",description:"Rank districts on one layer: top or bottom N, optionally within one province (Punjab, Sindh, KP, Balochistan, ICT). Skips estimates with fewer than 25 observations.",
  inputSchema:{type:"object",properties:{layer:{type:"string"},province:{type:"string"},n:{type:"number"},order:{type:"string",enum:["highest","lowest"]}},required:["layer"]},
  run:({layer,province,n,order})=>{ const L=B.layers[String(layer)]; if(!L) throw new Error("Unknown layer "+layer);
    const pv=province?String(province).replace(/khyber.*|kpk/i,"KP").replace(/islamabad/i,"ICT"):null;
    const rows=B.dist.filter(d=>d.v[layer]&&(L.noN||d.v[layer][1]>=25)&&(!pv||d.p.toLowerCase()===pv.toLowerCase())).map(d=>[d.n,d.p,d.v[layer][0]]);
    rows.sort((a,b)=>order==="lowest"?a[2]-b[2]:b[2]-a[2]); const k=Math.min(Math.max(1,+n||10),40);
    return {layer,label:L.label,unit:L.unit,higher_is_better:L.hb==null?null:!L.hb,order:order||"highest",of:rows.length,rows:rows.slice(0,k),source:L.src}; }},
 {name:"get_table",description:"Rows of one data table (the data behind a chart): [series, geography, period, value, (unit), (note)]. Use filter words to keep matching rows only (all words must match series, geography or period).",
  inputSchema:{type:"object",properties:{key:{type:"string"},filter:{type:"string"},limit:{type:"number"}},required:["key"]},
  run:({key,filter,limit})=>{ const t=B.tables[String(key)]; if(!t) throw new Error("Unknown table "+key+". Use search.");
    const fw=norm(filter||"").split(" ").filter(Boolean); let rows=t.rows;
    if(fw.length) rows=rows.filter(r=>{ const s=norm(r.slice(0,3).join(" ")); return fw.every(w=>s.includes(w)); });
    const k=Math.min(Math.max(1,+limit||120),250); let out=rows.slice(0,k);
    while(out.length>10&&JSON.stringify(out).length>26000) out=out.slice(0,Math.floor(out.length*.7));
    return {key,title:t.title,units:t.units,source:t.src,columns:["series","geography","period","value"].concat(t.units.length>1?["unit"]:[]),matching:rows.length,returned:out.length,
      hint:!rows.length?"No rows matched the filter. Use words from the series, geography or period lists below.":out.length<rows.length?"More rows match; narrow the filter (e.g. a year, place or series name).":undefined,periods:rows.length?undefined:[t.pers[0],t.pers.at(-1)],geographies:rows.length?undefined:t.geos.slice(0,15),
      series:fw.length&&rows.length?undefined:t.inds.slice(0,30),rows:out}; }}
]; }

const RULES=`You are Munshi, the record-keeper of "Shumaar", a public app of Pakistan's development and economic data: precise, plain-spoken, never showy. You answer questions about that data. Use ONLY numbers returned by your tools; never use outside knowledge for figures. If the data is not there, say so in one sentence and name the closest thing that is.
How to work: call tools silently (write nothing before your final answer). Call search (or use an id from the catalog), then get_indicator / get_district / rank_districts / get_table. Use as few calls as possible.
How to answer: plain text, at most 120 words, no headings, no tables. Lead with the direct answer and the number, with its year or survey round. For a district, give the province and Pakistan figures for context. Mention the source in a few words in brackets. If an estimate rests on a small sample, say so. Never invent a district, year or value.
Finish with one final line, exactly in one of these forms, pointing to the best chart for this answer:
VIEW: ind:<indicator id>
VIEW: dist:<district name>|<layer code>
VIEW: table:<table key>
VIEW: none`;

return {makeBundle,catalog,search,tools,findDistrict,RULES,toks,norm,sig};
})();
export default AskCore;
