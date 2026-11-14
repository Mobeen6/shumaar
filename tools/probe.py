"""One-off: save SBP pages that list data files, and test EasyData API access, into data_raw/probe/."""
import os, urllib.request, re
HDR={'Accept':'text/html,application/json,*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)','Accept-Language':'en'}
D='data_raw/probe'; os.makedirs(D,exist_ok=True)
U={'ecodata_index.html':'https://www.sbp.org.pk/ecodata/index2.asp',
   'ecodata_index1.html':'https://www.sbp.org.pk/ecodata/index.asp',
   'easydata_nokey.txt':'https://easydata.sbp.org.pk/api/v1/series/TS_GP_PT_CPI_M.P00011516/data?format=csv',
   'easydata_home.html':'https://easydata.sbp.org.pk/'}
log=[]
for fn,u in U.items():
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=60); b=r.read()
        open(f'{D}/{fn}','wb').write(b); log.append(f'ok {fn} {r.status} {len(b)}')
    except Exception as e: log.append(f'fail {fn} {e}')
open(f'{D}/log.txt','w').write('\n'.join(log)+'\n'); print('\n'.join(log))
