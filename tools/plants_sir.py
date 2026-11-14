# Plant-wise capacity (SIR Table 5) and generation (Table 8) -> by fuel, FY2021-FY2025
import re,sys,json,difflib
L=open(sys.argv[1]).read().split('\n')
def num(t):
    t=re.sub(r'[*‡†#]','',t.strip().replace(',','').replace(' ',''))
    if re.fullmatch(r'[-.·]+',t) or t in('--','..','·-'): return 0.0
    try: return float(t)
    except: return None
def rows(a,b,nv):
    out=[]
    for l in L[a:b]:
        p=[x for x in re.split(r'\s{2,}',l.strip()) if x]
        if len(p)<nv+1: continue
        vals=[num(x) for x in p[-nv:]]
        if any(v is None for v in vals): continue
        if re.search(r'total|grand',p[0],re.I): continue
        out.append((p,vals))
    return out
def norm(s):
    s=s.lower().replace('i11','iii').replace('111','iii').replace('-11','-ii').replace(' 11',' ii').replace('-1','-i').replace('0pp','(ipp')
    s=re.sub(r'-ii(?=\b|\W|$)','-ii',s)
    s=s.replace('!!v','gy').replace('l!v','gy').replace('2:','g').replace('enerii','energy')
    return re.sub(r'[^a-z0-9]','',s)
a5,b5,a8,b8=map(int,sys.argv[3:7]); cap=rows(a5,b5,6); gen=rows(a8,b8,5)
# scrambled blocks in Table 5 (read from the page): 2021..2025
extra={'Uch Power':[586]*5,'Attock Gen.':[165]*5,'Atlas Power':[224,224,224,224,0],
 'Engro Powergen. Qadirpur':[227]*5,'Saif Power':[225]*5,
 'Gul Ahmed Electric':[0,50,50,50,50],'Liberty Wind Power-II':[0,50,50,50,50],
 'NASDA Green Energy':[0,50,50,50,50],'Metro 2 Wind Power':[0,50,50,50,50],'Huaneng Shandong Ruyi':[1320]*5}
C={(re.sub(r'\s*\(formerly.*','',p[0])):v[:6] for p,v in cap}
if '22' in sys.argv[1]:
    for k,v in {'Malakand-III (PEDO)':[81]*5,'Pehur (PEDO)':[18]*5,'Zhenfa Pakistan New Energy':[0,0,0,0,100],'Huaneng Shandong Ruyi':[1320]*5,'Port Qasim Electric Power':[1320]*5,'Bin Qasim TPS-I':[1260,1260,1260,1050,840]}.items(): C[k]=[float(x) for x in v]
if '25' in sys.argv[1]:
    for k,v in extra.items(): C[k]=[float(x) for x in v]
Cn={norm(k):k for k in C}
def fuel(f):
    f=f.lower()
    if 'bagasse' in f or 'biomass' in f: return 'Bagasse'
    if 'hydel' in f or 'hvdel' in f or 'hydro' in f: return 'Hydro'
    if 'coal' in f: return 'Coal'
    if 'rlng' in f or 'dual' in f: return 'Imported LNG'
    if 'gas' in f and 'rfo' not in f: return 'Local gas'
    if 'rfo' in f or f=='fo': return 'Furnace oil'
    if 'nuc' in f: return 'Nuclear'
    if 'wind' in f: return 'Wind'
    if 'solar' in f: return 'Solar'
    if 'bagasse' in f: return 'Bagasse'
    return None
plants=[];miss=[];G=[]
for p,v in gen:
    nm=p[0]; f=None
    if fuel(nm) and len(p)==6 and 'coal' in nm.lower(): nm='Huaneng Shandong Ruyi'; f='Coal'
    if nm.startswith('Port Qasim Electric'): f='Coal'
    if nm.startswith('%') or 'net-meter' in nm.lower() or 'import' in nm.lower(): continue
    for tok in p[1:-5]:
        if f: break
        f=fuel(tok)
    G.append((nm,f,v))
pairs=sorted(((difflib.SequenceMatcher(None,norm(g[0]),k).ratio(),i,k) for i,g in enumerate(G) for k in Cn),reverse=True)
gi={};uk=set()
for sc,i,k in pairs:
    if i in gi or k in uk or sc<0.55: continue
    gi[i]=(k,sc);uk.add(k)
for i,(nm,f,v) in enumerate(G):
    if i not in gi or not f: miss.append((nm,f)); continue
    k,sc=gi[i]
    plants.append({'n':nm,'f':f,'mw':C[Cn[k]],'gwh':v,'cn':Cn[k],'sc':round(sc,2)})
# multi-line names
print(len(plants),'plants; unmatched:',miss,file=sys.stderr)
json.dump(plants,open(sys.argv[2],'w'))
