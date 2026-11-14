"""Build calendar.json and calendar.ics: upcoming official data releases.
Official dates: SBP data calendar ("Not Later Than"), SBP MPC calendar, SBP weekly reserves (every Thursday).
Usual timing (PBS has no published calendar for these): CPI on the first working day of the month, SPI every Friday."""
import re, json, os, datetime as dt
from bs4 import BeautifulSoup
D='data_raw/cal'; today=dt.date.today()
MON={m:i for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],1)}
HEAD=[(r"^Inflation Monitor","Inflation Monitor (SBP analysis of CPI)"),(r"^Official Reserve Assets","Foreign exchange reserves, month-end"),
 (r"^Country wise-Workers' Remittances","Workers' remittances"),(r"^Pakistan's Debt and Liabilities-Summary","Public debt and liabilities"),
 (r"^Summary of Balance of Payments BPM6","Balance of payments and current account"),(r"^Summary of Foreign Investment","Foreign investment (FDI and portfolio)"),
 (r"^Weighted Average Lending and Deposits Rates","Bank lending and deposit rates"),(r"^Monetary Aggregates \(M3\)","Money supply (M3)"),
 (r"^Bank Lending Survey","Bank Lending Survey"),(r"^Statistical Bulletin","SBP Statistical Bulletin"),(r"^Central Government Debt","Central government debt"),
 (r"^Savings Mobilized by National Savings","National Savings collections"),(r"^Nominal/Real Effective Exchange Rates","Real effective exchange rate"),
 (r"^Islamic Banking Bulletin","Islamic Banking Bulletin"),(r"^Payment Systems Review","Payment Systems Review"),(r"^Loans to Private Sector Business","Private sector credit by type"),
 (r"^Exports and Imports of Goods & Services","Exports and imports of goods and services")]
def per(s):
    m=re.search(r'for\s+(.*?)\s+Not Later',s); return m.group(1).replace('26',' 2026').replace('27',' 2027').replace('  ',' ').strip() if m else ''
ev=[]
# SBP data calendar
p=f'{D}/sbp_data_calendar.html'
if os.path.exists(p):
    rows=[' '.join(r.get_text(' ').split()) for r in BeautifulSoup(open(p,encoding='utf8',errors='ignore'),'html.parser').find('table').find_all('tr')]
    other={}
    for r in rows:
        m=re.search(r'Not Later Than\s+([A-Za-z]+)\s+(\d{1,2})\s+(20\d\d)',r)
        if not m: continue
        d=dt.date(int(m[3]),MON[m[1][:3].lower()],int(m[2]))
        nm=next((n for rx,n in HEAD if re.search(rx,r)),None)
        if nm: ev.append(dict(d=d.isoformat(),t=nm,ref=per(r),src='SBP',k='official',note='Not later than this date',url='https://www.sbp.org.pk/data-calendar'))
        else: other.setdefault(d.isoformat(),[]).append(re.sub(r'\s+for\s+.*$','',r))
    for d,l in other.items(): ev.append(dict(d=d,t=f'{len(l)} more SBP tables',ref='',src='SBP',k='official',note='; '.join(l),url='https://www.sbp.org.pk/data-calendar',minor=1))
# SBP MPC calendar
p=f'{D}/sbp_mpc_calendar.html'
if os.path.exists(p):
    txt=' '.join(BeautifulSoup(open(p,encoding='utf8',errors='ignore'),'html.parser').get_text(' ').split())
    i=txt.find('MPC Meeting Date'); j=txt.find('Note:',i); seg=txt[i:j]
    toks=re.findall(r'\d{2}-[A-Za-z]{3}-\d{2}|–',seg)
    # 6 columns per meeting: meeting, MPS, analyst briefing, press conference, minutes, MPR
    for k in range(0,len(toks)-5,6):
        row=toks[k:k+6]
        def dd(x): return dt.date(2000+int(x[7:9]),MON[x[3:6].lower()],int(x[:2])) if x!='–' else None
        m0,mins,mpr=dd(row[0]),dd(row[4]),dd(row[5])
        if m0: ev.append(dict(d=m0.isoformat(),t='Monetary policy decision (policy rate)',ref='',src='SBP',k='official',note='MPC meeting; statement, consumer and business confidence surveys released the same day',url='https://www.sbp.org.pk/m_policy/mp-calendar.asp',big=1))
        if mins: ev.append(dict(d=mins.isoformat(),t='MPC minutes',ref='',src='SBP',k='official',note='',url='https://www.sbp.org.pk/m_policy/mp-calendar.asp'))
        if mpr: ev.append(dict(d=mpr.isoformat(),t='Monetary Policy Report',ref='',src='SBP',k='official',note='',url='https://www.sbp.org.pk/m_policy/mp-calendar.asp'))
# rule-based: next 90 days
for i in range(-14,91):
    d=today+dt.timedelta(days=i)
    if d.weekday()==3: ev.append(dict(d=d.isoformat(),t='Liquid foreign exchange reserves (weekly)',ref='position on previous Friday',src='SBP',k='official',note='SBP releases every Thursday',url='https://www.sbp.org.pk/data-calendar',minor=1))
    if d.weekday()==4: ev.append(dict(d=d.isoformat(),t='Weekly prices (SPI)',ref='week to Thursday',src='PBS',k='usual',note='PBS usually publishes on Friday evening',url='https://www.pbs.gov.pk/spi'))
    if d.day<=3 and d.weekday()<5 and all((d-dt.timedelta(days=x)).weekday()>=5 for x in range(1,d.day)):
        pm=(d.replace(day=1)-dt.timedelta(days=1))
        ev.append(dict(d=d.isoformat(),t='Inflation (CPI)',ref=pm.strftime('%b %Y'),src='PBS',k='usual',note='PBS usually publishes on the first working day of the month',url='https://www.pbs.gov.pk/cpi',big=1))
# keep earlier official events already in calendar.json (the SBP page only lists the current month)
old=json.load(open('calendar.json')).get('ev',[]) if os.path.exists('calendar.json') else []
seen={(e['d'],e['t']) for e in ev}
ev+= [e for e in old if (e['d'],e['t']) not in seen and e['d']>=(today-dt.timedelta(days=120)).isoformat()]
ev.sort(key=lambda e:(e['d'],-e.get('big',0),e.get('minor',0),e['t']))
json.dump(dict(updated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),ev=ev),open('calendar.json','w'),separators=(',',':'))
# iCalendar feed (all-day events, upcoming only)
def esc(s): return s.replace('\\','\\\\').replace(',','\\,').replace(';','\\;').replace('\n','\\n')
L=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//shumaar.org//Data releases//EN','CALSCALE:GREGORIAN','X-WR-CALNAME:Pakistan data releases (Shumaar)','X-WR-TIMEZONE:Asia/Karachi']
for e in ev:
    if e.get('minor') or e['d']<(today-dt.timedelta(days=30)).isoformat(): continue
    d=dt.date.fromisoformat(e['d']); uid=re.sub(r'[^a-z0-9]','',(e['d']+e['t']).lower())[:60]+'@shumaar.org'
    title=f"{e['src']}: {e['t']}"+(f" ({e['ref']})" if e['ref'] else '')+(' [usual timing]' if e['k']=='usual' else '')
    L+=['BEGIN:VEVENT',f'UID:{uid}',f'DTSTAMP:{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}',f'DTSTART;VALUE=DATE:{d:%Y%m%d}',f'DTEND;VALUE=DATE:{d+dt.timedelta(days=1):%Y%m%d}',
        f'SUMMARY:{esc(title)}',f"DESCRIPTION:{esc((e['note']+' ' if e['note'] else '')+e['url'])}",'TRANSP:TRANSPARENT','END:VEVENT']
L.append('END:VCALENDAR')
open('calendar.ics','w',newline='').write('\r\n'.join(L)+'\r\n')
print(len(ev),'events')
