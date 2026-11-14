"""Parse PBS Monthly Review on Price Indices (data_raw/pbs_cpi/*_review.pdf) into cpi.json:
national CPI YoY (Table 1.a) and urban core NFNE YoY (Table 1.b). Later reviews override earlier ones (revisions)."""
import pdfplumber, re, glob, json, datetime as dt
MON={m:i for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],1)}
row=re.compile(r'^([A-Za-z]{3,9})[-\s]?(\d{2})\s+(-?\d+\.\d)\s')
cpi={}; core={}; src={}
for f in sorted(glob.glob('data_raw/pbs_cpi/*_review.pdf')):
    try: pdf=pdfplumber.open(f)
    except Exception: continue
    mode=None
    for pg in pdf.pages[:8]:
        for line in (pg.extract_text() or '').split('\n'):
            l=line.strip()
            if re.match(r'Table 1\.a',l): mode='cpi'; continue
            if re.match(r'Table 1\.b',l): mode='core'; continue
            if re.match(r'Table 1\.[1-9c]',l) or l.startswith('Table 2'): mode=None; continue
            m=row.match(l)
            if mode and m and m[1][:3].lower() in MON:
                k=f'20{m[2]}-{MON[m[1][:3].lower()]:02d}'; v=float(m[3])
                (cpi if mode=='cpi' else core)[k]=v; src[k]=f[-21:-14]
json.dump({'src':'Pakistan Bureau of Statistics, Monthly Review on Price Indices','updated':dt.date.today().isoformat(),
           'cpi':dict(sorted(cpi.items())),'core':dict(sorted(core.items()))},open('cpi.json','w'),separators=(',',':'))
print(len(cpi),min(cpi),max(cpi),len(core),min(core),max(core))
