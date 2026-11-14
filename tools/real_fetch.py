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
# OCAC statistics page and any data files on it
oc=links('https://www.ocac.org.pk/oil-industry-statistics/')
open(f'{D}/ocac_links.txt','w').write('\n'.join(oc))
for h in oc:
    if re.search(r'\.(xlsx?|pdf)$',h,re.I):
        fn=f"{D}/ocac_{re.sub(r'[^A-Za-z0-9._-]','_',h.rsplit('/',1)[1])}"
        if not os.path.exists(fn):
            b=get(h)
            if b: open(fn,'wb').write(b); log.append(f'ok ocac {fn}')
# SBP daily KIBOR: keep only the parsed rates
K=f'{D}/kibor.json'; kib=json.load(open(K)) if os.path.exists(K) else {}
try:
    import pdfplumber, io
    d=dt.date(2021,1,1)
    n=0
    while d<=dt.date.today() and n<400:
        if d.weekday()<5 and d.isoformat() not in kib:
            u=f"https://www.sbp.org.pk/assets/document/kibor-rates-{d.day}-{d.strftime('%B').lower()}-{d.year}.pdf"
            b=get(u,30); n+=1
            if b and b[:4]==b'%PDF':
                t=pdfplumber.open(io.BytesIO(b)).pages[0].extract_text() or ''
                m=re.search(r'6\s*-?\s*M(?:onths?)?\s+([\d.]+)\s+([\d.]+)',t,re.I)
                kib[d.isoformat()]={'bid':float(m[1]),'offer':float(m[2])} if m else {'raw':t[:300]}
            else: kib[d.isoformat()]=None
        d+=dt.timedelta(days=1)
    json.dump(kib,open(K,'w'))
    log.append(f'kibor dates {len(kib)} with rate {sum(1 for v in kib.values() if v and "offer" in v)}')
except Exception as e: log.append(f'kibor error {e}')
open(f'{D}/log.txt','a').write('\n'.join(log)+'\n'); print('\n'.join(log[-40:]))
