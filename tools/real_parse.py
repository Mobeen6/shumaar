"""Parse official real-sector files in data_raw/real/ into real.json, then update tracker.json series that come from them."""
import pandas as pd, json, re, os, glob, datetime as dt, warnings
warnings.filterwarnings('ignore')
D='data_raw/real/'; R={}
# PBS large-scale manufacturing quantum index (2015-16 = 100)
if os.path.exists(D+'pbs_qim_series.xlsx'):
    d=pd.read_excel(D+'pbs_qim_series.xlsx',header=None)
    R['lsm']={f'{v.year}-{v.month:02d}':round(float(q),3) for v,q in zip(d[0],d[1]) if isinstance(v,(pd.Timestamp,dt.datetime)) and q==q}
# PAMA monthly sales: total cars and total 2/3 wheelers. Each report covers the months of the fiscal year so far
# and the same months a year earlier. Digits in these PDFs are split into touching words, so words are re-joined by position.
try:
    import pdfplumber
    MO={m:i for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],1)}
    def lines(pg):
        w=sorted(pg.extract_words(x_tolerance=1),key=lambda x:x['top']); rows=[]
        for x in w:   # cluster words into rows by vertical position
            if rows and abs(x['top']-rows[-1][0])<=4.5: rows[-1][1].append(x)
            else: rows.append([x['top'],[x]])
        out=[]
        for _,row in rows:
            row=sorted(row,key=lambda x:x['x0']); m=[]
            for x in row:
                if m and -1.5<x['x0']-m[-1]['x1']<1.2: m[-1]={'text':m[-1]['text']+x['text'],'x0':m[-1]['x0'],'x1':x['x1']}
                else: m.append(dict(x))
            out.append([x['text'] for x in m])
        return out
    cars={}; bikes={}
    for f in sorted(glob.glob(D+'pama_20??-??.pdf')):
        hdr=None
        for pg in pdfplumber.open(f).pages:
            for t in lines(pg):
                mons=[x for x in t if re.match(r"^[A-Za-z]{3,9}'\d{2}$",x)]
                if len(mons)>=2: hdr=[(x.split("'")[0][:3].lower(),int(x.split("'")[1])) for x in mons]
                nums=[int(x.replace(',','')) if re.match(r'^[\d,]+$',x) else None for x in t if re.match(r'^([\d,]+|-)$',x)]
                isc=t[0]=='CARS' and len(nums)>=6; isb=t[0]=='Wheelers' and len(nums)>=6
                if (isc or isb) and hdr and nums:
                    n=len(hdr); half=n//2   # columns: months (prev FY), cumulative, months (this FY), cumulative
                    vals=nums[:half]+nums[half+1:half+1+half]
                    for (mo,yy),v in zip(hdr,vals):
                        if v is None: continue
                        y=2000+yy; key=f'{y}-{MO[mo]:02d}'
                        (cars if isc else bikes)[key]=v
    R['cars']=dict(sorted(cars.items())); R['bikes']=dict(sorted(bikes.items()))
except Exception as e: print('pama',e)
# SBP KIBOR 6-month offer, monthly average of daily sheets (keys are dates; older entries keyed by URL)
K=D+'kibor.json'
if os.path.exists(K):
    acc={}
    for k,v in json.load(open(K)).items():
        if not v or 'offer' not in v: continue
        m=re.match(r'(\d{4})-(\d{2})-\d{2}$',k)
        if m: acc.setdefault(f'{m[1]}-{m[2]}',[]).append(v['offer']); continue
        m=re.search(r'(\d{1,2})-([A-Za-z]{3})-(\d{2})\.pdf',k)
        if m: acc.setdefault(f'20{m[3]}-{pd.to_datetime(m[2],format="%b").month:02d}',[]).append(v['offer'])
    R['kibor']={k:round(sum(a)/len(a),3) for k,a in sorted(acc.items())}
# SBP EasyData downloads (daily KIBOR offer; REER/NEER, 2010=100) take precedence where present
E='data_raw/easydata/'
if os.path.exists(E+'kibor_offer_daily.csv'):
    k=pd.read_csv(E+'kibor_offer_daily.csv'); k=k[k['Series Key'].str.endswith('KIBOR0030')]
    k['m']=pd.to_datetime(k['Observation Date'],format='%d-%b-%Y').dt.strftime('%Y-%m')
    ed=k.groupby('m')['Observation Value'].mean().round(3).to_dict()
    R['kibor']={**R.get('kibor',{}),**ed}
if os.path.exists(E+'reer_neer_2010.csv'):
    f=pd.read_csv(E+'reer_neer_2010.csv'); mm=[pd.to_datetime(c,format='%b-%Y').strftime('%Y-%m') for c in f.columns[2:]]
    for lab,key in [('REER','reer'),('NEER','neer')]:
        row=f[f.ITEMS.str.contains(lab)&~f.ITEMS.str.contains('MOM')].iloc[0,2:]
        R[key]={m:round(float(v),2) for m,v in zip(mm,pd.to_numeric(row,errors='coerce')) if pd.notna(v)}
json.dump(dict(updated=dt.date.today().isoformat(),s=R),open('real.json','w'),separators=(',',':'))
# tracker: replace series that now come from the original publisher
T=json.load(open('tracker.json'))
SRC={'lsm':'PBS','cars':'PAMA','bikes':'PAMA','kibor':'SBP','reer':'SBP'}
if os.path.exists('cpi.json'):
    C=json.load(open('cpi.json'))
    for k in ('cpi','core'): R[k]=C[k]; SRC[k]='PBS'
for k,src in SRC.items():
    s={m:v for m,v in R.get(k,{}).items() if m>='2021-01'}
    if len(s)>=12:
        T[k]['m']=sorted(s); T[k]['v']=[s[m] for m in T[k]['m']]; T[k]['src']=src
json.dump(T,open('tracker.json','w'),separators=(',',':'))
print({k:(len(v),max(v) if v else None) for k,v in R.items()}, {k:T[k].get('src') for k in T})
