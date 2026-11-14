"""Parse official real-sector files in data_raw/real/ into real.json, then update tracker.json series that come from them."""
import pandas as pd, json, re, os, glob, datetime as dt, warnings
warnings.filterwarnings('ignore')
D='data_raw/real/'; R={}
# PBS large-scale manufacturing quantum index (2015-16 = 100)
if os.path.exists(D+'pbs_qim_series.xlsx'):
    d=pd.read_excel(D+'pbs_qim_series.xlsx',header=None)
    R['lsm']={f'{v.year}-{v.month:02d}':round(float(q),3) for v,q in zip(d[0],d[1]) if isinstance(v,(pd.Timestamp,dt.datetime)) and q==q}
# PAMA monthly sales: cars (passenger cars total) and motorcycles + rickshaws
try:
    import pdfplumber
    cars={}; bikes={}
    for f in sorted(glob.glob(D+'pama_20??-??.pdf')):
        k=os.path.basename(f)[5:12]; t='\n'.join((p.extract_text() or '') for p in pdfplumber.open(f).pages)
        n=lambda pat: next((int(m.replace(',','')) for m in re.findall(pat,t,re.I)),None)
        c=n(r'Total\s+Cars?\s+(?:[\d,]+\s+){0,3}?([\d,]{3,})') ; b=n(r'Total\s+(?:2\s*&\s*3\s*Wheelers|Motorcycles?\s*&?\s*Three\s*Wheelers)\s+(?:[\d,]+\s+){0,3}?([\d,]{4,})')
        if c: cars[k]=c
        if b: bikes[k]=b
    R['cars']=cars; R['bikes']=bikes
except Exception as e: print('pama',e)
# SBP KIBOR 6-month offer, monthly average of daily sheets
K=D+'kibor.json'
if os.path.exists(K):
    acc={}
    for u,v in json.load(open(K)).items():
        if not v or 'offer' not in v: continue
        m=re.search(r'(\d{1,2})[-_ ]?([A-Za-z]{3,9})[-_ ]?(\d{2,4})',u.rsplit('/',1)[1]) or (re.search(r'(\d{1,2})[-\s/.]([A-Za-z]{3,9})[-\s/.,]*(\d{2,4})',v.get('date') or ''))
        if not m: continue
        try: mo=pd.to_datetime(m[2][:3],format='%b').month
        except Exception: continue
        y=int(m[3]); y=y+2000 if y<100 else y; acc.setdefault(f'{y}-{mo:02d}',[]).append(v['offer'])
    R['kibor']={k:round(sum(a)/len(a),3) for k,a in sorted(acc.items())}
json.dump(dict(updated=dt.date.today().isoformat(),s=R),open('real.json','w'),separators=(',',':'))
# tracker: replace series that now come from the original publisher
T=json.load(open('tracker.json'))
SRC={'lsm':'PBS','cars':'PAMA','bikes':'PAMA','kibor':'SBP'}
if os.path.exists('cpi.json'):
    C=json.load(open('cpi.json'))
    for k in ('cpi','core'): R[k]=C[k]; SRC[k]='PBS'
for k,src in SRC.items():
    s={m:v for m,v in R.get(k,{}).items() if m>='2021-01'}
    if len(s)>=12:
        T[k]['m']=sorted(s); T[k]['v']=[s[m] for m in T[k]['m']]; T[k]['src']=src
json.dump(T,open('tracker.json','w'),separators=(',',':'))
print({k:(len(v),max(v) if v else None) for k,v in R.items()}, {k:T[k].get('src') for k in T})
