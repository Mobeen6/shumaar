"""Fetch SBP's own published data files (sbp.org.pk/ecodata) into data_raw/sbp/."""
import os, urllib.request
HDR={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)','Accept-Language':'en'}
D='data_raw/sbp'; os.makedirs(D,exist_ok=True)
B='https://www.sbp.org.pk/assets/document/'
FILES=['Homeremit_Arch.xlsx','BPM6_Ach_M.xlsx','M3-Arch.xlsx','BroadMoney_M2_Arch.xls','Forex_Arch.xlsx','ORA_Arch.xlsx',
       'BFER_Daily_Arch.xlsx','Lendingdepositrates_Arch.xls','IR-Corridor-Hist.xls','ExportsImports-Goods-Arch.xlsx','QGDP.xlsx','GDP_table.xlsx']
log=[]
for f in FILES:
    try:
        b=urllib.request.urlopen(urllib.request.Request(B+f,headers=HDR),timeout=90).read()
        open(f'{D}/{f}','wb').write(b); log.append(f'ok {f} {len(b)}')
    except Exception as e: log.append(f'fail {f} {e}')
open(f'{D}/log.txt','w').write('\n'.join(log)+'\n'); print('\n'.join(log))
