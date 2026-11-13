"""Parse PBS SPI Appendix-A (consumer prices of 51 essential items in 17 cities) into spi.json.
Uses the AVG column for each city; 0 or blank means not reported that week."""
import openpyxl, re, os, json, glob, datetime as dt
D='data_raw/spi'
def parse(f):
    ws=openpyxl.load_workbook(f,data_only=True,read_only=True)['Appendix-A']
    cols={}; out={}; units={}; names={}
    for r in ws.iter_rows(values_only=True):
        r=list(r)
        heads=[(i,re.sub(r'\s*\(\d+\)\s*$','',str(v)).strip()) for i,v in enumerate(r) if isinstance(v,str) and re.search(r'\(\d{2}\)\s*$',v)]
        if heads: cols={i:c for i,c in heads}; continue
        if isinstance(r[0],(int,float)) and r[0]==int(r[0]) and 1<=r[0]<=60 and isinstance(r[1],str) and cols:
            k=int(r[0]); names[k]=' '.join(r[1].split()); units[k]=' '.join(str(r[2]).split())
            for i,c in cols.items():
                v=r[i+1] if i+1<len(r) else None
                if isinstance(v,(int,float)) and v>0: out.setdefault(c,{})[k]=round(float(v),2)
    return names,units,out
def national(tag):
    """PBS's own national average price per item, from the SPI report (Page 2)."""
    fs=[f for f in glob.glob(f'{D}/{tag}__*.xlsx') if 'Annex' not in f]
    if not fs: return {}
    wb=openpyxl.load_workbook(fs[0],data_only=True,read_only=True); m={}
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            r=list(r)+[None]*6
            if isinstance(r[1],(int,float)) and isinstance(r[2],str) and isinstance(r[4],(int,float)):
                m[re.sub(r'[^a-z0-9]','',r[2].lower())]=round(float(r[4]),2)
    return m
files=sorted(glob.glob(f'{D}/*Annex*.xlsx'))
weeks={}; N={}; U={}; NAT={}
for f in files:
    tag=os.path.basename(f)[:10]
    try: n,u,o=parse(f)
    except Exception as e: print('fail',f,e); continue
    if len(o)<10: print('few cities',f,len(o)); continue
    weeks[tag]=o; N.update(n); U.update(u); NAT[tag]=national(tag)
cities=sorted({c for w in weeks.values() for c in w})
items=sorted(N)
json.dump({'src':'Pakistan Bureau of Statistics, weekly Sensitive Price Indicator, Appendix-A (average prices)',
  'updated':dt.date.today().isoformat(),'weeks':sorted(weeks),'cities':cities,
  'items':[{'id':k,'n':N[k],'u':U[k]} for k in items],
  'pk':{w:[NAT[w].get(re.sub(r'[^a-z0-9]','',N[k].lower())) for k in items] for w in sorted(weeks)},
  'p':{w:{c:[weeks[w].get(c,{}).get(k) for k in items] for c in cities} for w in sorted(weeks)}},
  open('spi.json','w'),separators=(',',':'))
print(len(weeks),'weeks',len(cities),'cities',len(items),'items')
