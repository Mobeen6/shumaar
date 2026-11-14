"""Fetch official real-sector and money-market sources into data_raw/real/:
PBS LSM (QIM trend sheet), PAMA monthly vehicle sales PDFs, OCAC statistics page and files, SBP daily KIBOR PDFs (values cached)."""
import os, re, json, urllib.request, urllib.parse, html, datetime as dt
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
# SBP daily KIBOR: each month's index page lists that month's daily PDFs; read the 6-month bid/offer from each.
# Values are cached by date and saved as we go, so a cut-off run keeps what it got.
K=f'{D}/kibor.json'; kib=json.load(open(K)) if os.path.exists(K) else {}
kib={k:v for k,v in kib.items() if v and 'offer' in v and not k.startswith('http')}
def fnum(x):
    x=re.sub(r'\.{2,}','.',x)
    try: return float(x)
    except: return None
def kib_date(u):
    m=re.search(r'(\d{1,2})[-_ ]([A-Za-z]{3})[a-z]*[-_ ](\d{2,4})\.pdf',u,re.I)
    if not m: return None
    y=int(m[3]); y=y+2000 if y<100 else y
    try: return dt.datetime.strptime(f'{int(m[1])} {m[2][:3].title()} {y}','%d %b %Y').date().isoformat()
    except: return None
try:
    import pdfplumber, io
    n=0; m0=dt.date(2021,1,1); today=dt.date.today()
    while m0<=today and n<2500:
        mon=m0.strftime('%b'); pdfs=set()
        for base in ['https://www.sbp.org.pk/ecodata/kibor','https://archive.sbp.org.pk/ecodata/kibor','https://www.sbp.org.pk/Ecodata/kibor']:
            idx=f'{base}/{m0.year}/{mon}/index.asp'
            for h in links(idx):
                if h.lower().endswith('.pdf'): pdfs.add(urllib.parse.urljoin(idx,h))
            if pdfs: break
        for u in sorted(pdfs):
            key=kib_date(u)
            if not key or key in kib: continue
            b=get(u,30); n+=1
            if not b or b[:4]!=b'%PDF': continue
            try: t=pdfplumber.open(io.BytesIO(b)).pages[0].extract_text() or ''
            except Exception: continue
            rm=re.search(r'6\s*-?\s*M[A-Za-z]*\s+([\d.]+)\s+([\d.]+)',t,re.I)
            if rm and fnum(rm[2]): kib[key]={'bid':fnum(rm[1]),'offer':fnum(rm[2])}
        log.append(f'kibor {m0:%Y-%m}: {len(pdfs)} files')
        json.dump(kib,open(K,'w'))
        m0=(m0.replace(day=28)+dt.timedelta(days=4)).replace(day=1)
    log.append(f'kibor days with rate {len(kib)}, requests {n}')
except Exception as e: log.append(f'kibor error {e}')
open(f'{D}/log.txt','a').write('\n'.join(log)+'\n'); print('\n'.join(log[-40:]))
