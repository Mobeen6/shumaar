"""Fetch official real-sector and money-market sources into data_raw/real/:
PBS LSM (QIM trend sheet), PAMA monthly vehicle sales PDFs, OCAC statistics page and files, SBP daily KIBOR PDFs (values cached)."""
import os, re, json, urllib.request, html, datetime as dt
HDR={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)','Accept-Language':'en'}
D='data_raw/real'; os.makedirs(D,exist_ok=True); log=[]
def get(u,t=90):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=t).read()
    except Exception as e: log.append(f'fail {u} {e}'); return None
def links(page):
    b=get(page); 
    return [html.unescape(h).strip() for h in re.findall(r'href=["\']([^"\']+)["\']',b.decode('utf8','ignore'))] if b else []
# PBS LSM trend sheet
for h in links('https://www.pbs.gov.pk/industry-2/'):
    if re.search(r'QIM-Series.*\.xlsx$',h,re.I):
        b=get(h); 
        if b: open(f'{D}/pbs_qim_series.xlsx','wb').write(b); log.append(f'ok qim {h}')
        break
# PAMA monthly production and sales PDFs
pama=[h for h in links('https://pama.org.pk/monthly-production-sales-of-vehicles/') if re.search(r'\.pdf\s*$',h,re.I)]
open(f'{D}/pama_links.txt','w').write('\n'.join(pama))
for h in pama:
    h=h.strip(); fn=f"{D}/pama_{re.sub(r'[^A-Za-z0-9._-]','_',h.rsplit('/',1)[1])}"
    if re.search(r'write',h,re.I) or os.path.exists(fn): continue
    b=get(h)
    if b and b[:4]==b'%PDF': open(fn,'wb').write(b); log.append(f'ok pama {fn}')
# PAMA: monthly files are named Production-Sales-<Month>-<Year>.pdf and uploaded the following month
m0=dt.date(2021,1,1)
while m0<dt.date.today().replace(day=1):
    fn=f"{D}/pama_{m0:%Y-%m}.pdf"
    if not os.path.exists(fn):
        for k in (1,2,0):
            y,mo=m0.year,m0.month+k; y+=(mo-1)//12; mo=(mo-1)%12+1; up=dt.date(y,mo,1)
            done=False
            for nm in (f"Production-Sales-{m0:%B}-{m0.year}",f"Production-Sales-{m0:%B}-{m0:%y}",f"Production-and-Sales-{m0:%B}-{m0.year}",f"Production-Sales-{m0:%b}-{m0.year}"):
                b=get(f"https://pama.org.pk/wp-content/uploads/{up:%Y}/{up:%m}/{nm}.pdf",30)
                if b and b[:4]==b'%PDF': open(fn,'wb').write(b); log.append(f'ok pama {m0:%Y-%m} {nm}'); done=True; break
            if done: break
    m0=(m0.replace(day=28)+dt.timedelta(days=5)).replace(day=1)
# OCAC statistics page and any data files on it
oc=links('https://www.ocac.org.pk/oil-industry-statistics/')
open(f'{D}/ocac_links.txt','w').write('\n'.join(oc))
for h in oc:
    if re.search(r'\.(xlsx?|pdf)$',h,re.I):
        fn=f"{D}/ocac_{re.sub(r'[^A-Za-z0-9._-]','_',h.rsplit('/',1)[1])}"
        if not os.path.exists(fn):
            b=get(h)
            if b: open(fn,'wb').write(b); log.append(f'ok ocac {fn}')
# SBP daily KIBOR: monthly index pages list the daily PDFs; keep only the parsed rates (plus a text sample if parsing fails)
K=f'{D}/kibor.json'; kib=json.load(open(K)) if os.path.exists(K) else {}
kib={k:v for k,v in kib.items() if v}   # drop earlier misses
try:
    import pdfplumber, io
    m0=dt.date(2021,1,1); n=0
    while m0<=dt.date.today() and n<700:
        mon=m0.strftime('%b'); pages=[f'https://www.sbp.org.pk/ecodata/kibor/{m0.year}/{mon}/index.asp',f'https://archive.sbp.org.pk/ecodata/kibor/{m0.year}/{mon}/index.asp']
        pdfs=[]
        for pg in pages:
            for h in links(pg):
                if h.lower().endswith('.pdf') and 'kibor' in h.lower():
                    pdfs.append(h if h.startswith('http') else pg.rsplit('/',1)[0]+'/'+h.lstrip('./'))
            if pdfs: break
        for u in sorted(set(pdfs)):
            if u in kib: continue
            b=get(u,40); n+=1
            if not (b and b[:4]==b'%PDF'): continue
            t=pdfplumber.open(io.BytesIO(b)).pages[0].extract_text() or ''
            dm=re.search(r'(\d{1,2})[-\s/.]([A-Za-z]{3,9})[-\s/.,]*(\d{2,4})',t)
            rm=re.search(r'6\s*-?\s*M[A-Za-z]*\s+([\d.]+)\s+([\d.]+)',t,re.I)
            kib[u]={'date':dm.group(0) if dm else None,'bid':float(rm[1]),'offer':float(rm[2])} if rm else {'raw':t[:400]}
        m0=(m0.replace(day=28)+dt.timedelta(days=5)).replace(day=1)
    json.dump(kib,open(K,'w'))
    log.append(f'kibor files {len(kib)} with rate {sum(1 for v in kib.values() if "offer" in v)}')
except Exception as e: log.append(f'kibor error {e}')
open(f'{D}/log.txt','a').write('\n'.join(log)+'\n'); print('\n'.join(log[-40:]))
