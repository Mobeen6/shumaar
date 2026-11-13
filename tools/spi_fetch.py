"""Fetch PBS weekly SPI reports (official) into data_raw/spi/.
PBS posts one page per week: /weekly-sensitive-price-indicator-spi-for-the-week-ended-on-DD-MM-YYYY/
Each page links the report files. Usage: python tools/spi_fetch.py [weeks_back]"""
import re, os, sys, urllib.request, html, datetime as dt
HDR={'Accept':'text/html,application/pdf,*/*'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=60).read()
D='data_raw/spi'; os.makedirs(D,exist_ok=True)
weeks=int(sys.argv[1]) if len(sys.argv)>1 else 4
log=[]
# week-ended dates are Thursdays; start from the latest Thursday on or before today
t=dt.date.today(); t-=dt.timedelta(days=(t.weekday()-3)%7)
for i in range(weeks):
    d=t-dt.timedelta(weeks=i); tag=d.strftime('%Y-%m-%d')
    if any(f.startswith(tag) for f in os.listdir(D)): continue
    page=f"https://www.pbs.gov.pk/weekly-sensitive-price-indicator-spi-for-the-week-ended-on-{d:%d-%m-%Y}/"
    try: h=get(page).decode('utf8','ignore')
    except Exception as e: log.append(f'{tag} page {e}'); continue
    files=sorted({html.unescape(x) for x in re.findall(r'href=["\']([^"\']+\.(?:pdf|xlsx?|docx?))["\']',h,re.I)})
    log.append(f'{tag} page ok, {len(files)} files: '+' | '.join(files))
    for u in files:
        if not u.startswith('http'): u='https://www.pbs.gov.pk'+u
        fn=f"{D}/{tag}__"+re.sub(r'[^A-Za-z0-9._-]','_',u.rsplit('/',1)[1])
        try: open(fn,'wb').write(get(u)); log.append(f'  got {fn}')
        except Exception as e: log.append(f'  fail {u} {e}')
open(f'{D}/log.txt','a').write('\n'.join(log)+'\n'); print('\n'.join(log))
