"""Parse PBS Monthly Review on Price Indices (data_raw/pbs_cpi/*_review.pdf) into cpi.json.
Table 1.a: YoY for national, urban, rural CPI, food and non-food (urban, rural), SPI, WPI.
Table 1.b: core NFNE YoY (urban, rural). Later reviews override earlier ones (revisions)."""
import pdfplumber, re, glob, json, datetime as dt
MON={m:i for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],1)}
row=re.compile(r'^([A-Za-z]{3,9})[-\s]?(\d{2})((?:\s+-?\d+\.\d+)+)\s*$')
A=['cpi','urb','rur','ufood','rfood','unf','rnf','spi','wpi']; B=['core','rcore']
S={k:{} for k in A+B}
for f in sorted(glob.glob('data_raw/pbs_cpi/*_review.pdf')):
    try: pdf=pdfplumber.open(f)
    except Exception: continue
    mode=None
    for pg in pdf.pages[:8]:
        for line in (pg.extract_text() or '').split('\n'):
            l=line.strip()
            if re.match(r'Table 1\.a',l): mode='a'; continue
            if re.match(r'Table 1\.b',l): mode='b'; continue
            if re.match(r'Table 1\.[1-9c]',l) or l.startswith('Table 2'): mode=None; continue
            m=row.match(l)
            if not (mode and m and m[1][:3].lower() in MON): continue
            k=f'20{m[2]}-{MON[m[1][:3].lower()]:02d}'; v=[float(x) for x in m[3].split()]
            keys=A if mode=='a' else B
            for i,key in enumerate(keys):
                if 2*i<len(v): S[key][k]=v[2*i]
json.dump({'src':'Pakistan Bureau of Statistics, Monthly Review on Price Indices','updated':dt.date.today().isoformat(),
           **{k:dict(sorted(v.items())) for k,v in S.items()}},open('cpi.json','w'),separators=(',',':'))
print({k:(len(v),min(v) if v else None,max(v) if v else None) for k,v in S.items()})
