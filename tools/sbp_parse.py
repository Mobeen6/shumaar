"""Parse SBP's published Excel files (data_raw/sbp/) into sbp.json: monthly series keyed 'YYYY-MM'."""
import pandas as pd, json, re, datetime as dt, warnings
warnings.filterwarnings('ignore')
D='data_raw/sbp/'
def mkey(v):
    if isinstance(v,(pd.Timestamp,dt.datetime,dt.date)): return f'{v.year}-{v.month:02d}'
    s=str(v).strip()
    m=re.match(r'([A-Za-z]+)[ ,\-]+(\d{2,4})(?!\d)',s)
    if m:
        try:
            mo=pd.to_datetime(m[1][:3],format='%b').month; y=int(m[2]); y=y+2000 if y<100 else y; return f'{y}-{mo:02d}'
        except Exception: return None
    return None
def num(v):
    try: f=float(v); return None if f!=f else f
    except Exception: return None
S={}
# remittances: total cash inflow, all sheets
x=pd.read_excel(D+'Homeremit_Arch.xlsx',sheet_name=None,header=None)
rem={}
for sh,d in x.items():
    hr=next(i for i in range(len(d)) if sum(mkey(v) is not None for v in d.iloc[i])>3)
    tr=next(i for i in range(hr+1,len(d)) if any(str(v).strip().lower().startswith('cash') for v in d.iloc[i,:3]))
    for j,v in enumerate(d.iloc[hr]):
        k=mkey(v); val=num(d.iat[tr,j])
        if k and val is not None: rem[k]=round(val,2)
S['rem']=rem
# remittances by source country (top-level rows)
GRP={'USA':r'^USA','UK':r'^U\.?K\.?$','Saudi Arabia':r'^Saudi','UAE':r'^U\.?A\.?E','Other Gulf':r'^Other GCC','EU':r'^EU Count'}
for g,pat in GRP.items():
    acc={}
    for sh,d in x.items():
        hr=next(i for i in range(len(d)) if sum(mkey(v) is not None for v in d.iloc[i])>3)
        rr=[i for i in range(hr+1,len(d)) if re.match(pat,str(d.iat[i,2]).strip()) and str(d.iat[i,1]).strip() not in ('nan','')]
        if not rr: continue
        for j,v in enumerate(d.iloc[hr]):
            k=mkey(v); val=num(d.iat[rr[0],j])
            if k and val is not None: acc[k]=round(val,2)
    S['rem_'+g]=acc
# balance of payments (BPM6 summary, monthly)
d=pd.read_excel(D+'BPM6_Ach_M.xlsx',header=None)
hr=next(i for i in range(len(d)) if sum(mkey(v) is not None for v in d.iloc[i])>3)
def row(pat):
    i=next(i for i in range(hr+1,len(d)) if re.match(pat,str(d.iat[i,0]).strip(),re.I))
    return {mkey(v):num(d.iat[i,j]) for j,v in enumerate(d.iloc[hr]) if mkey(v) and num(d.iat[i,j]) is not None}
S['ca']=row(r'Current account balance$|Current account balance\s*$'); S['x']=row(r'Exports of goods'); S['m']=row(r'Imports of goods')
# reserves: month-end liquid reserves
d=pd.read_excel(D+'Forex_Arch.xlsx',sheet_name='Month-end',header=None)
res_sbp={}; res_tot={}
prev=None
for i in range(len(d)):
    k=mkey(d.iat[i,1])
    if k and num(d.iat[i,2]) is not None:
        if prev and k<=prev:   # SBP sometimes mislabels the year (e.g. 'Jan 25' after 'Dec 25'); rows are in order
            y,mo=map(int,prev.split('-')); mo+=1; y+=mo>12; mo=(mo-1)%12+1; k=f'{y}-{mo:02d}'
        prev=k; res_sbp[k]=round(num(d.iat[i,2])/1e3,3); res_tot[k]=round(num(d.iat[i,4])/1e3,3)
S['res']=res_sbp; S['res_tot']=res_tot
# exchange rate: monthly average of daily banks' average rate, US dollar
d=pd.read_excel(D+'BFER_Daily_Arch.xlsx',header=None)
hr=next(i for i in range(len(d)) if str(d.iat[i,0]).strip()=='Country')
r=next(i for i in range(hr+1,len(d)) if 'U.S' in str(d.iat[i,0]) or 'United States' in str(d.iat[i,0]) or str(d.iat[i,1]).strip().lower().startswith('us dollar'))
acc={}
for j,v in enumerate(d.iloc[hr]):
    if isinstance(v,(pd.Timestamp,dt.datetime)) and num(d.iat[r,j]) is not None: acc.setdefault(mkey(v),[]).append(num(d.iat[r,j]))
S['usd']={k:round(sum(a)/len(a),3) for k,a in acc.items()}

# broad money, end-June stocks (Rs million), all archive sheets
x=pd.read_excel(D+'BroadMoney_M2_Arch.xls',sheet_name=None,header=None)
ROWS={'cur':r'^Currency in','m2':r'^Broad Money','nfa':r'^Net Foreign','nda':r'^Net Domestic','gov':r'^\d?\.?\s*Net Government','priv':r'^a\.\s*Credit to Private','dem':r'^(\(i\)\s*)?Demand Dep','time':r'^(\(ii\)\s*)?Time Dep','rfcd':r'^(\(iii\)\s*)?Resident'}
m2fy={}
for sh,d in x.items():
    hr=next(i for i in range(len(d)) if sum(isinstance(v,(pd.Timestamp,dt.datetime)) for v in d.iloc[i])>3)
    lab=[(' '.join(str(d.iat[i,c]) for c in (1,2) if str(d.iat[i,c])!='nan')).strip() for i in range(len(d))]
    rows={k:next((i for i in range(hr+1,len(d)) if any(re.match(pat,str(d.iat[i,c]).strip(),re.I) for c in (1,2))),None) for k,pat in ROWS.items()}
    june={}
    for j,v in enumerate(d.iloc[hr]):
        if isinstance(v,(pd.Timestamp,dt.datetime)) and v.month==6: june[v.year]=j   # last June column wins
    for y,j in june.items():
        r=m2fy.setdefault(y,{})
        for k,i in rows.items():
            if i is not None and num(d.iat[i,j]) is not None: r[k]=num(d.iat[i,j])
S['m2fy']={str(y):v for y,v in sorted(m2fy.items())}
out={k:dict(sorted(v.items())) for k,v in S.items()}
json.dump(dict(updated=dt.date.today().isoformat(),src='State Bank of Pakistan, published data files (sbp.org.pk/ecodata)',s=out),open('sbp.json','w'),separators=(',',':'))
for k,v in out.items(): print(k,len(v),list(v.items())[-2:])
