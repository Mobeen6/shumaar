"""Fetch official release calendars (SBP data calendar, SBP MPC calendar, PBS release statements) into data_raw/cal/."""
import os, urllib.request, datetime as dt
HDR={'Accept':'text/html,application/pdf,*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)','Accept-Language':'en'}
D='data_raw/cal'; os.makedirs(D,exist_ok=True)
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=HDR),timeout=60).read()
t=dt.date.today(); months=[dt.date(2026,9,1),(t.replace(day=1)-dt.timedelta(days=1)).replace(day=1), t.replace(day=1), (t.replace(day=28)+dt.timedelta(days=5)).replace(day=1)]
urls={'sbp_data_calendar.html':'https://www.sbp.org.pk/data-calendar',
      'sbp_mpc_calendar.html':'https://www.sbp.org.pk/m_policy/mp-calendar.asp'}
for m in months:
    urls[f'pbs_release_statement_{m:%Y-%m}.pdf']=f'https://www.pbs.gov.pk/wp-content/uploads/2020/07/Release_Statement_{m:%B}-{m:%Y}.pdf'
log=[]
for fn,u in urls.items():
    try: b=get(u); open(f'{D}/{fn}','wb').write(b); log.append(f'ok {fn} {len(b)}')
    except Exception as e: log.append(f'fail {fn} {u} {e}')
open(f'{D}/log.txt','w').write('\n'.join(log)+'\n'); print('\n'.join(log))
