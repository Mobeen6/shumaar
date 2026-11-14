"""SBP EasyData API: download listed series to data_raw/easydata/<id>.csv. Key from env SBP_EASYDATA_KEY (never written out).
On each run also probes catalogue endpoints so series keys can be found; responses are saved with the key stripped."""
import os, re, json, urllib.request, urllib.parse, datetime as dt
KEY=os.environ.get('SBP_EASYDATA_KEY','').strip()
D='data_raw/easydata'; os.makedirs(D,exist_ok=True); log=[]
B='https://easydata.sbp.org.pk/api/v1'
def get(u,t=60):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={'Accept':'*/*','User-Agent':'python-requests/2.32.3','Accept-Encoding':'identity'}),timeout=t)
        return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()[:2000]
    except Exception as e: return None, str(e).encode()
def clean(b): return b.decode('utf8','ignore').replace(KEY,'<key>') if KEY else b.decode('utf8','ignore')
if not KEY: log.append('no key')
SERIES=json.load(open('tools/easydata_series.json')) if os.path.exists('tools/easydata_series.json') else {}
end=dt.date.today().isoformat()
for name,sid in SERIES.items():
    st,b=get(f'{B}/series/{urllib.parse.quote(sid)}/data?api_key={KEY}&start_date=2000-01-01&end_date={end}&format=csv')
    if st==200 and b and not b.lstrip().startswith(b'{'):
        open(f'{D}/{name}.csv','wb').write(b); log.append(f'ok {name} {sid} {len(b)}')
    else: log.append(f'fail {name} {sid} {st} {clean(b)[:200]}')
# probe catalogue endpoints (keys only in the request, stripped from what is saved)
probe=[]
for path in ['/datasets','/series','/catalog','/dataset','/datasets/list','/series/list','/categories']:
    st,b=get(f'{B}{path}?api_key={KEY}&format=json')
    probe.append(f'== {path} {st}\n{clean(b)[:20000]}')
open(f'{D}/probe.txt','w').write('\n\n'.join(probe))
open(f'{D}/log.txt','w').write('\n'.join(log)+'\n'); print('\n'.join(log))
