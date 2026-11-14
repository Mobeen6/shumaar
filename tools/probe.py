"""One-off: save pages that list official data files into data_raw/probe/ so the right file links can be found."""
import os, urllib.request
HDR={'Accept':'text/html,*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)','Accept-Language':'en'}
D='data_raw/probe'; os.makedirs(D,exist_ok=True)
U={'pbs_industry.html':'https://www.pbs.gov.pk/industry-2/',
   'pbs_qim_aug26.html':'https://www.pbs.gov.pk/summary-of-provisional-quantum-index-numbers-of-large-scale-manufacturing-industries-qim-for-aug-2026-2/',
   'sbp_kibor_index.html':'https://www.sbp.org.pk/ecodata/kibor_index.asp',
   'sbp_kibor_2026_oct.html':'https://www.sbp.org.pk/ecodata/kibor/2026/Oct/index.asp',
   'pama_home.html':'https://www.pama.org.pk/',
   'pama_stats.html':'https://www.pama.org.pk/statistical-information/',
   'ocac_home.html':'https://ocac.org.pk/',
   'nepra_home.html':'https://nepra.org.pk/',
   'sbp_neer.html':'https://www.sbp.org.pk/ecodata/NEER_REER.asp',
   'sbp_ecodata_er.html':'https://www.sbp.org.pk/ecodata/index2.asp#er'}
log=[]
for fn,u in U.items():
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=60); b=r.read()
        open(f'{D}/{fn}','wb').write(b); log.append(f'ok {fn} {len(b)}')
    except Exception as e: log.append(f'fail {fn} {e}')
open(f'{D}/log2.txt','w').write('\n'.join(log)+'\n'); print('\n'.join(log))
