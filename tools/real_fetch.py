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
# OCAC monthly files that may still sit in the same upload folder (the page links only the latest month)
d0=dt.date.today().replace(day=1)
for k in range(1,30):
    d0=(d0-dt.timedelta(days=1)).replace(day=1)
    for nm in [f"{d0:%b}-{d0.year}-Pak-Provinces.pdf",f"{d0:%B}-{d0.year}-Pak-Provinces.pdf"]:
        fn=f"{D}/ocac_{nm}"
        if os.path.exists(fn): break
        for up in ['2022/05',f'{d0.year}/{d0.month:02d}',f'{(d0+dt.timedelta(days=40)).year}/{(d0+dt.timedelta(days=40)).month:02d}']:
            b=get(f'https://www.ocac.org.pk/wp-content/uploads/{up}/{nm}',30)
            if b and b[:4]==b'%PDF': open(fn,'wb').write(b); log.append(f'ok ocac {fn}'); break
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
def kib_urls(d):
    a=d.strftime('%b'); yy=d.strftime('%y'); mon=d.strftime('%B').lower()
    return [f"https://www.sbp.org.pk/assets/document/kibor-rates-{d.day}-{mon}-{d.year}.pdf",
            f"https://www.sbp.org.pk/assets/document/kibor-rates-{d:%d}-{mon}-{d.year}.pdf",
            f"https://archive.sbp.org.pk/ecodata/kibor/{d.year}/{a}/kibor-{d:%d}-{a}-{yy}.pdf",
            f"https://www.sbp.org.pk/ecodata/kibor/{d.year}/{a}/Kibor-{d:%d}-{a}-{yy}.pdf"]
def kib_parse(b):
    t=pdfplumber.open(io.BytesIO(b)).pages[0].extract_text() or ''
    rm=re.search(r'6\s*-?\s*M[A-Za-z]*\s+([\d.]+)\s+([\d.]+)',t,re.I)
    if rm and fnum(rm[2]) and 1<fnum(rm[2])<40: return {'bid':fnum(rm[1]),'offer':fnum(rm[2])}
try:
    import pdfplumber, io
    n=0
    # 1) files linked from SBP's KIBOR page
    for u in [urllib.parse.urljoin('https://www.sbp.org.pk/',h) for h in links('https://www.sbp.org.pk/economic-data/kibor-rates') if h.lower().endswith('.pdf')]:
        key=kib_date(u) or (lambda m: m and dt.datetime.strptime(f'{m[1]} {m[2][:3].title()} {m[3]}','%d %b %Y').date().isoformat())(re.search(r'kibor-rates-(\d{1,2})-([a-z]+)-(\d{4})',u,re.I))
        if not key or key in kib: continue
        b=get(u,30); n+=1
        if b and b[:4]==b'%PDF':
            try:
                r=kib_parse(b)
                if r: kib[key]=r
            except Exception: pass
    # 2) every working day not yet held, trying each naming pattern (the last one that worked first)
    d=dt.date.today()-dt.timedelta(days=45); best=0; miss=json.load(open(f'{D}/kibor_miss.json')) if os.path.exists(f'{D}/kibor_miss.json') else []
    while d<=dt.date.today() and n<2500:
        key=d.isoformat()
        if d.weekday()<5 and key not in kib and key not in miss:
            urls=kib_urls(d); got=None
            for i in [best]+[i for i in range(len(urls)) if i!=best]:
                b=get(urls[i],25); n+=1
                if b and b[:4]==b'%PDF': got=(i,b); break
            if got:
                best=got[0]
                try:
                    r=kib_parse(got[1])
                    if r: kib[key]=r
                except Exception: pass
            elif d<dt.date.today()-dt.timedelta(days=7): miss.append(key)
            if n%100==0: json.dump(kib,open(K,'w'))
        d+=dt.timedelta(days=1)
    json.dump(kib,open(K,'w')); json.dump(miss,open(f'{D}/kibor_miss.json','w'))
    log.append(f'kibor days with rate {len(kib)}, misses {len(miss)}, requests {n}')
except Exception as e:
    json.dump(kib,open(K,'w')); log.append(f'kibor error {e}')
open(f'{D}/log.txt','a').write('\n'.join(log)+'\n'); print('\n'.join(log[-40:]))
