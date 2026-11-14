"""Fetch official reference documents (annual) into data_raw/docs/: NEPRA State of Industry and DISCO performance
reports, Bureau of Emigration yearly reports, Finance Division Budget in Brief, MNFSR Agricultural Statistics of Pakistan."""
import os, urllib.request, urllib.parse
HDR={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)','Accept-Language':'en'}
D='data_raw/docs'; os.makedirs(D,exist_ok=True); log=[]
def get(u):
    u=urllib.parse.quote(u,safe=':/?=&%')
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=180).read()
    except Exception as e: log.append(f'fail {u} {e}'); return None
U={'nepra_sir_2025.pdf':['https://www.nepra.org.pk/publications/State of Industry Reports/State of Industry Report 2025.pdf'],
   'nepra_per_disco_2024-25.pdf':['https://nepra.org.pk/M&E/PER/Distribution/2026/PER 2024-25 Distribution Companies.pdf'],
   'mnfsr_asp_2024-25.pdf':['https://mnfsr.gov.pk/SiteImage/Publication/ASP 2024-25 FINAL.pdf'],
   'budget_in_brief_2025-26.pdf':['https://finance.gov.pk/budget/budget_2025_26/budget_in_brief_10062025.pdf'],
   'budget_in_brief_2026-27.pdf':['https://finance.gov.pk/budget/budget_2026_27/budget_in_brief.pdf','https://www.finance.gov.pk/budget/budget_2026_27/budget_in_brief.pdf',
                                  'https://finance.gov.pk/budget/budget_2026_27/Budget_in_Brief_2026_27.pdf','https://finance.gov.pk/budget/budget_2026_27/budget_in_brief_2026_27.pdf']}
for y in range(2015,2027):
    U[f'beoe_{y}.pdf']=[f'https://beoe.gov.pk/files/statistics/yearly-reports/{y}/{y}-full.pdf',f'https://beoe.gov.pk/files/statistics/yearly-reports/{y}/{y}.pdf']
for fn,us in U.items():
    if os.path.exists(f'{D}/{fn}') or os.path.exists(f'{D}/{fn}.skipped'): continue
    for u in us:
        b=get(u)
        if b and b[:4]==b'%PDF':
            if len(b)>40e6:   # too big for the repository: keep the text of every page instead
                import pdfplumber, io, gzip
                txt='\n'.join(f'=== page {i+1}\n'+(pg.extract_text() or '') for i,pg in enumerate(pdfplumber.open(io.BytesIO(b)).pages))
                gzip.open(f'{D}/{fn[:-4]}.txt.gz','wt').write(txt); open(f'{D}/{fn}.skipped','w').write(str(len(b)))
                log.append(f'ok-text {fn} {len(b)}')
            else:
                open(f'{D}/{fn}','wb').write(b); log.append(f'ok {fn} {len(b)}')
            break
open(f'{D}/log.txt','a').write('\n'.join(log)+'\n'); print('\n'.join(log))
