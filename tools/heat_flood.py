"""Extreme heat days (ERA5-Land, geo/shumaar_gee_heat.js) and flood frequency 2000-2018 (Global Flood Database,
geo/shumaar_gee_floodfreq.js) -> heat.json + district layers."""
import json,pandas as pd,numpy as np,shapefile
r=shapefile.Reader('geo/shp/shumaar_districts_shp.shp'); M={x[0]:(x[1],x[2]) for x in r.records()}
dj=json.load(open('shumaar/districts.json'))
pop={int(f):v['c_pop'][0] for f,v in dj['vals'].items() if 'c_pop' in v}
h=pd.read_csv('build/heat.csv'); h['year']=h.year.astype(int)
yrs=sorted(h.year.unique().tolist())
out={'years':yrs,'d':{},'reg':{},'partial':int(h[h.year==yrs[-1]].days.iloc[0])}
for i,g in h.groupby('id'):
    g=g.set_index('year').reindex(yrs)
    out['d'][str(i)]={k:[round(x,1) for x in g[k].tolist()] for k in ('d40','d45','n30')}
REG=['Pakistan','Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan','Islamabad ICT','Gilgit-Baltistan','Azad Jammu & Kashmir']
for reg in REG:
    ids=[i for i in M if reg=='Pakistan' or M[i][1]==reg]
    w=np.array([pop.get(i,0) for i in ids],float)
    if w.sum()==0: continue
    sub=h[h.id.isin(ids)].copy(); sub['w']=sub.id.map(dict(zip(ids,w)))
    agg=sub.groupby('year').apply(lambda g: pd.Series({k:(g[k]*g.w).sum()/g.w.sum() for k in ('d40','d45','n30')})).reindex(yrs)
    out['reg'][reg]={k:[round(x,1) for x in agg[k]] for k in ('d40','d45','n30')}
def per(i,k,a,b): x=out['d'][str(i)][k]; return float(np.mean([x[yrs.index(y)] for y in range(a,b+1)]))
base={'src':'ERA5-Land reanalysis 1981-2025','theme':'Climate','hb':True,'rural':False,'noN':True,'tier':'model',
 'check':'ECMWF ERA5-Land reanalysis via Google Earth Engine, averaged over the district; a model reconstruction, smoother than single weather stations.'}
L={'ht_d45':('Days above 45 °C a year, 2011-2025 average','days a year','Days per year on which the daily maximum temperature, averaged over the district, exceeded 45 °C.'),
   'ht_n30':('Hot nights a year (minimum above 30 °C), 2011-2025 average','nights a year','Nights per year on which the temperature, averaged over the district, never fell below 30 °C.'),
   'ht_n30ch':('Change in hot nights a year, 2011-25 vs 1981-2010','nights a year','Hot nights (minimum above 30 °C) per year in 2011-2025 minus 1981-2010.')}
for c,(lab,u,o) in L.items(): dj['inds'][c]={**base,'label':lab,'unit':u,'orig':o}
for i in M:
    v=dj['vals'].setdefault(str(i),{})
    v['ht_d45']=[round(per(i,'d45',2011,2025),1),99999]; v['ht_n30']=[round(per(i,'n30',2011,2025),1),99999]
    v['ht_n30ch']=[round(per(i,'n30',2011,2025)-per(i,'n30',1981,2010),1),99999]
def rper(reg,k,a,b): x=out['reg'][reg][k]; return float(np.mean([x[yrs.index(y)] for y in range(a,b+1)]))
dj['prov']['ht_d45']={g:round(rper(g,'d45',2011,2025),1) for g in out['reg']}
dj['prov']['ht_n30']={g:round(rper(g,'n30',2011,2025),1) for g in out['reg']}
dj['prov']['ht_n30ch']={g:round(rper(g,'n30',2011,2025)-rper(g,'n30',1981,2010),1) for g in out['reg']}
# floods
f=pd.read_csv('build/floodfreq.csv').set_index('id')
SKIP={i for i in M if M[i][1] in ('Gilgit-Baltistan','Azad Jammu & Kashmir')}|{i for i in M if M[i][0] in ('Haripur','Tor Ghar','Swabi')}
fb={'src':'Global Flood Database 2000-2018','theme':'Climate','hb':True,'rural':False,'noN':True,'tier':'model',
 'check':'Global Flood Database (Tellman et al. 2021, Nature): large floods mapped from MODIS satellite images at 250 m, permanent water removed. Misses short flash floods and floods under cloud; ends in 2018, so the 2022 floods are not included. Mountain districts and the Tarbela reservoir edge are left out because snow, shadow and reservoir levels read as flooding.'}
dj['inds']['fl_ever']={**fb,'label':'Land flooded at least once, 2000-2018, %','unit':'% of district area','orig':'Share of the district\'s land mapped under flood water in at least one large flood, 2000-2018.'}
dj['inds']['fl_rep']={**fb,'label':'Land flooded three or more times, 2000-2018, %','unit':'% of district area','orig':'Share of the district\'s land mapped under flood water in three or more separate large floods, 2000-2018.'}
for i in M:
    v=dj['vals'].setdefault(str(i),{})
    for c in ('fl_ever','fl_rep'): v.pop(c,None)
    if i in SKIP or i not in f.index: continue
    v['fl_ever']=[round(100*f.at[i,'flood1_km2']/f.at[i,'area_km2'],1),99999]; v['fl_rep']=[round(100*f.at[i,'flood3_km2']/f.at[i,'area_km2'],1),99999]
P={}
for reg in ['Pakistan','Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan']:
    ids=[i for i in M if (reg=='Pakistan' or M[i][1]==reg) and i not in SKIP]
    a=f.loc[ids,'area_km2'].sum(); P[reg]=(round(100*f.loc[ids,'flood1_km2'].sum()/a,1),round(100*f.loc[ids,'flood3_km2'].sum()/a,1),round(f.loc[ids,'flood1_km2'].sum()),round(f.loc[ids,'flood3_km2'].sum()))
dj['prov']['fl_ever']={k:v[0] for k,v in P.items()}; dj['prov']['fl_rep']={k:v[1] for k,v in P.items()}
top=sorted([(round(100*f.at[i,'flood3_km2']/f.at[i,'area_km2'],1),i) for i in M if i not in SKIP and i in f.index],reverse=True)[:12]
out['flood']={'prov':P,'top':[[M[i][0],M[i][1],v,round(100*f.at[i,'flood1_km2']/f.at[i,'area_km2'],1)] for v,i in top]}
json.dump(out,open('shumaar/heat.json','w'),separators=(',',':'))
json.dump(dj,open('shumaar/districts.json','w'),separators=(',',':'),ensure_ascii=False)
print({k:[round(rper(k,'d45',1981,2010),1),round(rper(k,'d45',2011,2025),1),round(rper(k,'n30',1981,2010),1),round(rper(k,'n30',2011,2025),1)] for k in ['Pakistan','Punjab','Sindh','Balochistan','Khyber Pakhtunkhwa']})
print(P); print(out['flood']['top'][:6])
print(sorted([(dj['vals'][str(i)]['ht_n30ch'][0],M[i][0]) for i in M])[-8:])
