import urllib.request,os,re
os.makedirs('data_raw/real',exist_ok=True)
H={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)'}
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60).read()
    except Exception as e: return ('ERR '+str(e)).encode()
out=[]
for tag,u in [('fmd','https://www.sbp.org.pk/our-operations/financial-market/financial-market-data'),
              ('mmi','https://www.sbp.org.pk/our-operations/financial-market/money-market-instruments-operations'),
              ('ecodata','https://www.sbp.org.pk/ecodata/index2.asp')]:
    b=get(u); open(f'data_raw/real/kibor_idx_{tag}.html','wb').write(b)
    out+= [f'{tag} '+h for h in re.findall(r'href="([^"]+)"',b.decode('utf8','ignore')) if re.search(r'kibor|\.xls|\.pdf',h,re.I)]
for g in ['KIBOR_Arch.xlsx','Kibor_Arch.xlsx','KIBOR-Arch.xlsx','kibor_arch.xls','KIBOR_Arch.xls','Kibor-Rates-Arch.xlsx']:
    b=get('https://www.sbp.org.pk/assets/document/'+g); out.append(f'guess {g} {len(b)} {b[:8]!r}')
open('data_raw/real/kibor_probe.txt','w').write('\n'.join(out))
for t in ('2021feb','2024may','2026oct','index'):
    p=f'data_raw/real/kibor_idx_{t}.html'
    if os.path.exists(p): os.remove(p)
