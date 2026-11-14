"""Fetch official reference documents (annual) into data_raw/docs/: NEPRA State of Industry and DISCO performance
reports, Finance Division Budget in Brief, MNFSR Agricultural Statistics of Pakistan.
Files are streamed to disk; very large PDFs are kept only as text (pdftotext, low memory)."""
import os, sys, urllib.request, urllib.parse, subprocess, gzip, shutil
HDR={'Accept':'application/pdf,text/html,*/*','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36','Accept-Language':'en-US,en;q=0.9','Referer':'https://beoe.gov.pk/reports-and-statistics'}
D='data_raw/docs'; os.makedirs(D,exist_ok=True)
def log(m): print(m,flush=True); open(f'{D}/log.txt','a').write(m+'\n')
def fetch(u,dest):
    u=urllib.parse.quote(u,safe=':/?=&%')
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=120) as r, open(dest,'wb') as f: shutil.copyfileobj(r,f,1<<20)
        with open(dest,'rb') as f: ok=f.read(4)==b'%PDF'
        if not ok: os.remove(dest)
        return ok
    except Exception as e:
        log(f'fail {u} {e}'); 
        if os.path.exists(dest): os.remove(dest)
        return False
U={'nepra_sir_2025.pdf':['https://www.nepra.org.pk/publications/State of Industry Reports/State of Industry Report 2025.pdf'],
   **{f'nepra_sir_{y}.pdf':[f'https://www.nepra.org.pk/publications/State of Industry Reports/State of Industry Report {y}.pdf'] for y in range(2018,2025)},
   'nepra_per_disco_2024-25.pdf':['https://nepra.org.pk/M&E/PER/Distribution/2026/PER 2024-25 Distribution Companies.pdf'],
   'budget_in_brief_2025-26.pdf':['https://finance.gov.pk/budget/budget_2025_26/budget_in_brief_10062025.pdf'],
   'budget_in_brief_2026-27.pdf':['https://finance.gov.pk/budget/budget_2026_27/budget_in_brief.pdf','https://finance.gov.pk/budget/budget_2026_27/Budget_in_Brief_2026_27.pdf','https://finance.gov.pk/budget/budget_2026_27/budget_in_brief_2026_27.pdf'],
   'budget_in_brief_2024-25.pdf':['https://www.finance.gov.pk/budget/Budget_2024_25/Budget_in_Brief.pdf'],
   'budget_in_brief_2023-24.pdf':['https://www.finance.gov.pk/budget/Budget_2023_24/Budget_in_Brief.pdf'],
   'budget_in_brief_2022-23.pdf':['https://www.finance.gov.pk/budget/Budget_2022_23/Budget_in_Brief_English.pdf'],
   'mnfsr_asp_2024-25.pdf':['https://mnfsr.gov.pk/SiteImage/Publication/ASP 2024-25 FINAL.pdf']}
# Punjab Crop Reporting Service: district-wise history (area, production, yield)
for c in ['Wheat','Rice','Cotton','Sugarcane','Maize','Gram']:
    U[f'crs_punjab_{c.lower()}_2022-25.pdf']=[f'https://crs-agripunjab.punjab.gov.pk/system/files/Historical Data {c} (Districtwise) 2022-25.pdf',
        f'https://crs-agripunjab.punjab.gov.pk/system/files/Historical%20Data%20{c}%20%28Districtwise%29%202022-25.pdf']
U['crs_punjab_final_rabi_2023-24.pdf']=['https://agripunjab.punjab.gov.pk/system/files/Final Rabi Estimates 2023-24.pdf']
U['bos_punjab_pas_2024.pdf']=['https://bos.punjab.gov.pk/system/files/PAS 2024.pdf']
only=sys.argv[1:]  # optional: fetch only these names
for fn,us in U.items():
    if only and fn not in only: continue
    if os.path.exists(f'{D}/{fn}') or os.path.exists(f'{D}/{fn[:-4]}.txt.gz'): continue
    tmp=f'/tmp/{fn}'
    for u in us:
        if fetch(u,tmp):
            n=os.path.getsize(tmp)
            if n>40e6:
                subprocess.run(['pdftotext','-layout',tmp,f'/tmp/{fn}.txt'],check=False)
                with open(f'/tmp/{fn}.txt','rb') as a, gzip.open(f'{D}/{fn[:-4]}.txt.gz','wb') as b: shutil.copyfileobj(a,b)
                log(f'ok-text {fn} {n}')
            else:
                shutil.move(tmp,f'{D}/{fn}'); log(f'ok {fn} {n}')
            break
