"""Fetch PBS monthly CPI releases (Monthly Review on Price Indices, press release) into data_raw/pbs_cpi/.
PBS file names vary, so several spellings are tried for each month."""
import os, urllib.request, datetime as dt, sys
HDR={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)','Accept-Language':'en'}
D='data_raw/pbs_cpi'; os.makedirs(D,exist_ok=True)
B='https://www.pbs.gov.pk/wp-content/uploads/2020/07/'
start=dt.date(int(sys.argv[1]) if len(sys.argv)>1 else 2021,1,1); t=dt.date.today()
log=[]
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=60).read()
    except Exception: return None
d=start
while d<=t:
    M,Y=d.strftime('%B'),d.year
    tag=d.strftime('%Y-%m')
    for kind,names in (('review',[f'Monthly-Review-{M}-{Y}',f'Monthly-Review-{M}{Y}',f'Monthly-Review-{M}-{Y}-1',f'Monthly_Review_{M}_{Y}',f'CPI_Review_{M}_{Y}']),
                       ('press',[f'Press-Release-{M}-{Y}',f'Press-Release-{M}-{Y}-1',f'Press_Release_{M}_{Y}',f'CPI_Press_Release_{M}_{Y}'])):
        if any(f.startswith(f'{tag}_{kind}') for f in os.listdir(D)): continue
        got=False
        for n in names:
            for ext in ('.pdf','.docx'):
                b=get(B+n+ext)
                if b and len(b)>2000 and (b[:4]==b'%PDF' or b[:2]==b'PK'):
                    open(f'{D}/{tag}_{kind}{ext}','wb').write(b); log.append(f'ok {tag} {kind} {n}{ext}'); got=True; break
            if got: break
        if not got: log.append(f'miss {tag} {kind}')
    d=(d.replace(day=28)+dt.timedelta(days=5)).replace(day=1)
open(f'{D}/log.txt','a').write('\n'.join(log)+'\n'); print('\n'.join(log))
