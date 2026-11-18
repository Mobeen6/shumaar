import json,pandas as pd,numpy as np
from shapely.geometry import shape
from pyproj import Geod
G=Geod(ellps='WGS84'); gj=json.load(open('geo/shumaar_districts.geojson'))
A={};P={};N={}
for f in gj['features']:
    p=f['properties']; A[p['id']]=abs(G.geometry_area_perimeter(shape(f['geometry']))[0])/1e6; P[p['id']]=p['p']; N[p['id']]=p['n']
d=pd.read_csv('build/nl_monthly.csv')
w=d.pivot(index='m',columns='id',values='mean_nw'); w.index=pd.PeriodIndex(w.index,freq='M')
lr=w.mean()
dark=lr.nsmallest(20).index
bg=w[dark].median(axis=1)
net=w.sub(bg,axis=0).clip(lower=0)
area=pd.Series(A)
tot=net.mul(area[w.columns])
nat=tot.sum(axis=1)/1e3
def anom(s):
    tr=s.rolling(13,center=True,min_periods=7).mean(); r=s/tr
    return (r/r.groupby(r.index.month).transform('median')-1)*100
if __name__=='__main__':
    print('bg',bg.describe().round(3).to_dict())
    print(nat.groupby(nat.index.year).mean().round(0).to_string())
    an=anom(nat); print(an.round(1).sort_values().head(15).to_string())
    t=json.load(open('shumaar/tracker.json'))['elec']; g=pd.Series(t.get('v') or t.get('d'),index=pd.PeriodIndex(t['m'],freq='M'))
    j=pd.concat([nat,g],axis=1,keys=['nl','gen']).dropna()
    print(len(j),'level corr',j.corr().iloc[0,1].round(2),'yoy',j.pct_change(12).corr().iloc[0,1].round(2),'anom',pd.concat([anom(nat),anom(g)],axis=1).dropna().corr().iloc[0,1].round(2))
    print(j.round(0).to_string())

def build():
    yrs=list(range(2013,2027))
    def dip(s,y): return round((s[f'{y}-05':f'{y}-08'].mean()/s[f'{y-1}-11':f'{y}-02'].mean()-1)*100,1)
    kar=[i for i in N if 'Karachi' in N[i]]
    ser=lambda cols: net[cols].mul(area[cols]).sum(axis=1)
    out={'years':yrs,'Pakistan':[dip(nat,y) for y in yrs],'Karachi':[dip(ser(kar),y) for y in yrs],
         'Lahore':[dip(ser([111]),y) for y in yrs],'Islamabad':[dip(ser([59]),y) for y in yrs]}
    x=net.loc['2021-11':'2026-08']; mo=x.index.month
    r=(x[(mo>=5)&(mo<=8)].mean()/x[(mo>=11)|(mo<=2)].mean()-1)*100
    lit=lr[lr>1.0].index; rows=sorted([[N[i],P[i].replace('Khyber Pakhtunkhwa','KP').replace('Azad Jammu & Kashmir','AJK').replace('Islamabad ICT','ICT'),round(r[i],1)] for i in lit],key=lambda a:a[2])
    out['dist']=rows
    t=json.load(open('shumaar/tracker.json'))['elec']; g=pd.Series(t.get('v') or t.get('d'),index=pd.PeriodIndex(t['m'],freq='M'))
    j=pd.concat([nat,g],axis=1,keys=['nl','gen']).dropna(); out['corr']=round(j.corr().iloc[0,1],2); out['corrn']=len(j)
    out['last']=str(nat.index[-1])
    a=json.load(open('shumaar/agri.json')); a['nl']['dim']=out; json.dump(a,open('shumaar/agri.json','w'),separators=(',',':'))
    print(out)
if __name__=='__main__': build()
