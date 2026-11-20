"""Warming stripes from ERA5-Land monthly means of daily min/max by district (geo/shumaar_gee_temp.js).
Anomalies vs 1981-2010; regions area-weighted (geodesic district area)."""
import json,pandas as pd,numpy as np
from shapely.geometry import shape
from pyproj import Geod
G=Geod(ellps='WGS84'); gj=json.load(open('geo/shumaar_districts.geojson'))
A={};P={};N={}
for f in gj['features']:
    p=f['properties']; A[p['id']]=abs(G.geometry_area_perimeter(shape(f['geometry']))[0])/1e6; P[p['id']]=p['p']; N[p['id']]=p['n']
d=pd.read_csv('build/temp_monthly.csv'); d['y']=d.m.str[:4].astype(int); d['mo']=d.m.str[5:].astype(int)
d['a']=d.id.map(A); d['p']=d.id.map(P)
def region_monthly(g):
    w=g.a; return pd.Series({'tmin':(g.tmin*w).sum()/w.sum(),'tmax':(g.tmax*w).sum()/w.sum()})
R={}
R['Pakistan']=d.groupby(['y','mo']).apply(region_monthly)
for p in sorted(set(P.values())): R[p]=d[d.p==p].groupby(['y','mo']).apply(region_monthly)
for i in sorted(A): R[i]=d[d.id==i].set_index(['y','mo'])[['tmin','tmax']]
SEAS={'ann':range(1,13),'mjjas':range(5,10),'djf':[12,1,2],'mam':[3,4,5],'jja':[6,7,8],'son':[9,10,11]}
def series(df,sk):
    x=df.reset_index(); mos=list(SEAS[sk])
    if sk=='djf': x['y']=np.where(x.mo==12,x.y+1,x.y)   # Dec counts toward next winter
    x=x[x.mo.isin(mos)]; c=x.groupby('y').size(); g=x.groupby('y')[['tmin','tmax']].mean()[c==len(mos)]
    base=g.loc[1981:2010].mean() if sk!='djf' else g.loc[1982:2010].mean()
    return (g-base).round(2), base
out={'years':list(range(1981,2027)),'regions':{},'names':{},'rank':{}}
for k,df in R.items():
    key=str(k); out['names'][key]=N.get(k,k) if not isinstance(k,str) else k
    rec={}
    for sk in ('ann','mjjas'):
        a,base=series(df,sk); rec[sk]={'n':[a.tmin.get(y) for y in out['years']],'d':[a.tmax.get(y) for y in out['years']],'bn':round(base.tmin,1),'bd':round(base.tmax,1)}
    for sk in ('djf','mam','jja','son','ann','mjjas'):
        a,_=series(df,sk); rec.setdefault('rec',{})[sk]=[round(a.loc[2011:2025].tmin.mean(),2),round(a.loc[2011:2025].tmax.mean(),2)]
    out['regions'][key]=rec
# clean NaN -> None
def clean(o):
    if isinstance(o,dict): return {k:clean(v) for k,v in o.items()}
    if isinstance(o,list): return [clean(v) for v in o]
    if isinstance(o,float) and np.isnan(o): return None
    if isinstance(o,(np.floating,)): return None if np.isnan(o) else round(float(o),2)
    return o
out=clean(out); out['prov']={str(i):P[i] for i in A}
json.dump(out,open('shumaar/temp.json','w'),separators=(',',':'))
if __name__=='__main__':
    for k in ['Pakistan','Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan','Gilgit-Baltistan','Azad Jammu & Kashmir','Islamabad ICT']:
        if k not in out['regions']: continue
        r=out['regions'][k]; print(k, 'ann n/d 2025',r['ann']['n'][44],r['ann']['d'][44],'mjjas 2025',r['mjjas']['n'][44],r['mjjas']['d'][44],'2011-25',r['rec'])
