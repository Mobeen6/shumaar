"""Probe official school portals for school-level location data; save pages and link lists."""
import urllib.request,os,re
D='data_raw/schools_probe'; os.makedirs(D,exist_ok=True)
H={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)'}
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60).read()
    except Exception as e: return ('ERR '+str(e)).encode()
pages={'punjab_open':'http://www.open.punjab.gov.pk/schools/','punjab_open2':'https://open.punjab.gov.pk/schools/',
 'punjab_sis':'https://sis.punjab.gov.pk/','punjab_schools':'https://schools.punjab.gov.pk/',
 'kp_home':'https://kpese.gov.pk/','kp_maps':'https://kpese.gov.pk/maps/','kp_emis':'https://emis.kpese.gov.pk/','kp_ese':'https://www.ese.gok.pk/',
 'sindh_semis':'https://semis.rsu-sindh.gov.pk/','sindh_rsu':'https://rsusindh.gov.pk/',
 'bal_bemis':'https://www.bemis.edu.pk/','bal_pmu':'https://emis.balochistan.gov.pk/'}
out=[]
for k,u in pages.items():
    b=get(u); open(f'{D}/{k}.html','wb').write(b[:3_000_000])
    t=b.decode('utf8','ignore')
    out.append(f'== {k} {u} {len(b)} {t[:80]!r}')
    out+=[f'  {h}' for h in sorted(set(re.findall(r'(?:href|src)=["\']([^"\']+)["\']',t))) if re.search(r'kml|kmz|csv|xls|json|map|gis|school|api|download',h,re.I)][:80]
open(f'{D}/links.txt','w').write('\n'.join(out))
