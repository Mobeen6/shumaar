# MNFSR "Crops Area and Production (by districts)" 2024-25: district area ('000 ha) and production (latest year)
import re,sys,json
L=open(sys.argv[1]).read().split('\n')
spans={'Wheat':(506,658),'Rice':(658,807),'Sugarcane':(1399,1546),'Cotton':(1546,1694)}
PROV={'PUNJAB':'Punjab','SINDH':'Sindh','KHYBER':'Khyber Pakhtunkhwa','KPK':'Khyber Pakhtunkhwa','BALOCHISTAN':'Balochistan'}
out={}
for crop,(a,b) in spans.items():
    prov=None; rows={}
    for l in L[a:b]:
        t=l.strip(); up=t.upper()
        for k,v in PROV.items():
            if up.startswith(k) and not re.search(r'\d',t.split('  ')[0]): prov=v
        if re.match(r'(Province|Total|PAKISTAN|Grand)',t,re.I): continue
        m=re.match(r'([A-Za-z][A-Za-z .\'&/()-]+?)\s{2,}(.*)$',t)
        if not m or not prov: continue
        nums=re.findall(r'-?[\d,]*\.?\d+',m.group(2))
        if len(nums)<8: continue
        v=[float(x.replace(',','')) for x in nums[:8]]
        # columns: area 23-24, %, area 24-25, %, prod 23-24, %, prod 24-25, %
        rows[(prov,m.group(1).strip())]={'a':v[2],'p':v[6],'a0':v[0],'p0':v[4]}
    out[crop]=rows
    print(crop,len(rows),file=sys.stderr)
json.dump({c:[[k[0],k[1],r['a'],r['p'],r['a0'],r['p0']] for k,r in d.items()] for c,d in out.items()},open(sys.argv[2],'w'))
