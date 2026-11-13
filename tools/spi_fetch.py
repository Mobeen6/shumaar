"""Fetch PBS weekly SPI reports (official) into data_raw/spi/. Lists links found in data_raw/spi/links.txt."""
import re, os, sys, urllib.request, html
HDR={'Accept':'text/html,application/pdf,*/*'}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=60).read()
os.makedirs('data_raw/spi',exist_ok=True)
pages=['https://www.pbs.gov.pk/spi','https://www.pbs.gov.pk/spi-detail','https://www.pbs.gov.pk/']
links=set(); log=[]
for p in pages:
    try:
        t=get(p).decode('utf8','ignore'); log.append(f'{p} ok {len(t)}')
        for h in re.findall(r'href=["\']([^"\']+)["\']',t):
            h=html.unescape(h)
            if 'spi' in h.lower(): links.add(h if h.startswith('http') else 'https://www.pbs.gov.pk'+('' if h.startswith('/') else '/')+h)
    except Exception as e: log.append(f'{p} ERR {e}')
open('data_raw/spi/links.txt','w').write('\n'.join(log+sorted(links)))
def key(u):
    m=re.search(r'(\d{1,2})[._-](\d{1,2})[._-](20\d\d)',u)
    return (int(m[3]),int(m[2]),int(m[1])) if m else (0,0,0)
pdfs=sorted([u for u in links if u.lower().endswith(('.pdf','.xlsx','.xls'))],key=key,reverse=True)
n=0
for u in pdfs[:int(sys.argv[1]) if len(sys.argv)>1 else 6]:
    fn='data_raw/spi/'+re.sub(r'[^A-Za-z0-9._-]','_',u.rsplit('/',1)[1])
    if os.path.exists(fn): continue
    try: open(fn,'wb').write(get(u)); n+=1; print('got',fn)
    except Exception as e: print('fail',u,e)
print('new files',n)
