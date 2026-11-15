"""Official school locations: Sindh RSU online GIS (Google My Maps per district, exported as KML);
probes Punjab school census portal and KP annual school census pages."""
import urllib.request,urllib.parse,os,re,json
D='data_raw/schools'; os.makedirs(D+'/sindh_kml',exist_ok=True)
H={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)'}
def get(u,t=90):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=t).read()
    except Exception as e: return ('ERR '+str(e)).encode()
log=[]
base='https://rsusindh.gov.pk/programs/onlineGIS.php?district='
t=get(base+'Karachi%20Central').decode('utf8','ignore')
dists=sorted(set(re.findall(r'onlineGIS\.php\?district=([^"\'&]+)',t)))
mids={}
for d in dists:
    page=get(base+urllib.parse.quote(urllib.parse.unquote(d))).decode('utf8','ignore')
    ms=re.findall(r'maps/d/(?:u/\d+/)?embed\?mid=([\w-]+)',page)
    mids[urllib.parse.unquote(d)]=ms
    for mid in ms:
        fn=f'{D}/sindh_kml/{mid}.kml'
        if os.path.exists(fn): continue
        b=get(f'https://www.google.com/maps/d/kml?mid={mid}&forcekml=1',180)
        if b.startswith(b'<?xml') or b'<kml' in b[:500]: open(fn,'wb').write(b); log.append(f'kml {d} {mid} {len(b)}')
        else: log.append(f'kml fail {d} {mid} {b[:80]!r}')
json.dump(mids,open(f'{D}/sindh_mids.json','w'),indent=1)
for k,u in {'punjab_sed_census':'https://schoolportal.punjab.gov.pk/sed_census/','kp_asc_2425':'https://kpese.gov.pk/annual-schools-statistical-report-2024-25/','kp_asc_2324':'https://kpese.gov.pk/annual-school-census-2023-24/'}.items():
    b=get(u); open(f'{D}/{k}.html','wb').write(b[:3_000_000]); t=b.decode('utf8','ignore')
    log.append(f'== {k} {len(b)} {t[:60]!r}')
    log+=[f'  {h}' for h in sorted(set(re.findall(r'(?:href|src|action)=["\']([^"\']+)["\']',t))) if re.search(r'kml|csv|xls|json|pdf|map|gis|emis|school|api|download|\.php',h,re.I) and 'wp-includes' not in h][:100]
open(f'{D}/log.txt','w').write('\n'.join(log))
