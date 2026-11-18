"""Brick kilns by district (Hamdani et al. 2024, Zenodo 14038648, CC BY 4.0) and dust share of PM2.5
(NASA MERRA-2 composition, calibrated to AQLI's dust-free PM2.5 for 25 districts)."""
import json,pandas as pd,numpy as np
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
from pyproj import Geod
G=Geod(ellps='WGS84'); gj=json.load(open('geo/shumaar_districts.geojson'))
F=[(f['properties'],shape(f['geometry'])) for f in gj['features']]
area={p['id']:abs(G.geometry_area_perimeter(g)[0])/1e6 for p,g in F}
N={p['id']:p['n'] for p,_ in F}; P={p['id']:p['p'] for p,_ in F}
tree=STRtree([g for _,g in F])
k=pd.read_csv('kiln/main.csv',encoding='utf-8-sig')
def dist(r):
    pt=Point(r.lon,r.lat)
    for i in tree.query(pt):
        if F[i][1].contains(pt): return F[i][0]['id']
    i=tree.nearest(pt); return F[i][0]['id'] if F[i][1].distance(pt)<0.05 else None
k['d']=k.apply(dist,axis=1); print('unplaced',k.d.isna().sum(), len(k))
k['zz']=k.type.str.upper().isin(['ZZ','ZIGZAG']); k['sch']=k.schools1km>0
g=k.groupby('d').agg(n=('id','size'),zz=('zz','mean'),sch=('sch','mean'))
g['den']=g.n/pd.Series(area).reindex(g.index)*1000
dj=json.load(open('shumaar/districts.json'))
dj['inds']['kl_den']={'label':'Brick kilns per 1,000 km²','src':'Satellite kiln map (2023)','theme':'Climate','hb':True,'unit':'kilns per 1,000 km²','rural':False,'noN':True,
 'orig':'Brick kilns detected in July 2023 Sentinel-2 imagery and confirmed on high-resolution images (Hamdani et al. 2024, Brick Kiln Dataset for Pakistan\'s IGP Region, Zenodo, CC BY 4.0), counted by district. Covers the Indus plain in Punjab, Sindh and KP; Balochistan and the hills were not searched, so blank there does not mean none.'}
dj['inds']['kl_zz']={'label':'Brick kilns converted to zigzag firing, %','src':'Satellite kiln map (2023)','theme':'Climate','hb':False,'unit':'% of kilns','rural':False,'noN':True,
 'orig':'Share of kilns with zigzag (induced-draught) firing rather than the older fixed-chimney Bull\'s trench design, from the shape of the kiln in satellite images (Hamdani et al. 2024, Zenodo, CC BY 4.0). Zigzag kilns burn less coal and emit less soot. Districts with at least 20 kilns.'}
for fid in dj['vals']:
    for c in ('kl_den','kl_zz','sat_pmnd','sat_dust'): dj['vals'][fid].pop(c,None)
for d_,r in g.iterrows():
    v=dj['vals'].setdefault(str(int(d_)),{})
    v['kl_den']=[round(r.den,1),99999]
    if r.n>=20: v['kl_zz']=[round(r.zz*100,1),99999]
kp=k.assign(p=k.d.map(P)).groupby('p').agg(n=('id','size'),zz=('zz','mean'),sch=('sch','mean'))
pa=pd.Series(area).groupby(pd.Series(P)).sum()
dj['prov']['kl_den']={'Pakistan':round(len(k)/sum(area.values())*1000,1),**{p:round(r.n/pa[p]*1000,1) for p,r in kp.iterrows() if r.n>=50}}
dj['prov']['kl_zz']={'Pakistan':round(k.zz.mean()*100,1),**{p:round(r.zz*100,1) for p,r in kp.iterrows() if r.n>=50}}
# ---- dust ----
d=pd.read_csv('build/pm_dust.csv'); d['tot']=d[['dust','seasalt','bc','om','so4']].sum(axis=1); d['ds']=(d.dust+d.seasalt)/d.tot
y=d[(d.season=='year')&(d.year==2022)].set_index('id')
pm=pd.Series({int(f):v['sat_pm'][0] for f,v in dj['vals'].items() if 'sat_pm' in v})
aq=pd.Series({int(f):v['aq_pm'][0] for f,v in dj['vals'].items() if 'aq_pm' in v})
z=pd.DataFrame({'ds':y.ds,'impl':1-aq/pm}).dropna(); b=np.polyfit(z.ds,z.impl,1)
sh=pd.Series(np.clip(np.polyval(b,y.ds.values),0.05,0.8),index=y.index)
for fid,s in sh.items():
    if fid in pm.index:
        v=dj['vals'][str(fid)]; v['sat_dust']=[round(s*100,1),99999]; v['sat_pmnd']=[round(pm[fid]*(1-s),1),99999]
dj['inds']['sat_pmnd']={'label':'PM2.5 excluding dust and sea salt (estimated), 2022','src':'Satellite PM2.5 2022, modelled split','theme':'Climate','hb':True,'unit':'µg/m³','rural':False,'noN':True,
 'orig':'Satellite total PM2.5 (ACAG/WashU V6.GL.02) minus an estimated dust and sea-salt share. The share comes from NASA MERRA-2 aerosol reanalysis (2022 mean surface dust, sea salt, black carbon, organic matter and sulphate), rescaled so that it reproduces AQLI\'s dust-free figures for the 25 districts AQLI publishes (typical error about 8 percentage points). An estimate, not a measurement.'}
dj['inds']['sat_dust']={'label':'Dust and sea salt, share of PM2.5 (estimated), 2022','src':'Satellite PM2.5 2022, modelled split','theme':'Climate','hb':True,'unit':'%','rural':False,'noN':True,'orig':dj['inds']['sat_pmnd']['orig']}
ps=pd.Series(dj['prov']['sat_pm']); 
# province: population-weighted would need pop; use district-mean share by province
shp=pd.Series(sh).groupby(pd.Series(P)).mean()
dj['prov']['sat_dust']={p:round(shp[p]*100,1) for p in ps.index if p in shp}
dj['prov']['sat_pmnd']={p:round(ps[p]*(1-shp[p]),1) for p in ps.index if p in shp}
natsh=float(pd.Series(sh).mean()); dj['prov']['sat_dust']['Pakistan']=round(natsh*100,1); dj['prov']['sat_pmnd']['Pakistan']=round(ps['Pakistan']*(1-natsh),1)
json.dump(dj,open('shumaar/districts.json','w'),separators=(',',':'),ensure_ascii=False)
# panel data
sea=d[d.season!='year'].copy(); sea['p']=sea.p
sp=sea.groupby(['p','season']).dust.median().unstack()
top=g.sort_values('n',ascending=False).head(12)
out={'n':len(k),'zz':round(k.zz.mean()*100,1),'sch':round(k.sch.mean()*100,1),
 'top':[[N[i],P[i].replace('Khyber Pakhtunkhwa','KP'),int(r.n),round(r.zz*100)] for i,r in top.iterrows()],
 'prov':[[p.replace('Khyber Pakhtunkhwa','KP'),int(r.n),round(r.zz*100,1)] for p,r in kp.sort_values('n',ascending=False).iterrows()],
 'dust':[[p.replace('Khyber Pakhtunkhwa','KP'),round(sp.loc[p,'nov-jan'],1),round(sp.loc[p,'apr-jun'],1)] for p in ['Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan','Islamabad ICT']],
 'calib':[round(b[0],3),round(b[1],3)],'pmt':dict(ps),'pmnd':dj['prov']['sat_pmnd'],'dsh':dj['prov']['sat_dust']}
s=json.load(open('shumaar/env.json')) if False else None
a=json.load(open('shumaar/agri.json')); a['kiln']=out; json.dump(a,open('shumaar/agri.json','w'),separators=(',',':'),ensure_ascii=False)
print(json.dumps(out,ensure_ascii=False)); print(dj['prov']['kl_den'])
