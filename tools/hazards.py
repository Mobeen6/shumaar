"""Multi-hazard exposure (hot nights, unhealthy air, repeat floods) and hazard-vs-outcome rank correlations."""
import json,numpy as np,pandas as pd,shapefile
from scipy.stats import spearmanr
r=shapefile.Reader('geo/shp/shumaar_districts_shp.shp'); M={x[0]:(x[1],x[2]) for x in r.records()}
dj=json.load(open('shumaar/districts.json')); V=dj['vals']
g=lambda i,c: V.get(str(i),{}).get(c,[None])[0]
TH={'ht_n30':10,'pm_d55':150,'fl_rep':2.0}
rows=[]
for i in M:
    f={c:(g(i,c) is not None and g(i,c)>=t) for c,t in TH.items()}
    rows.append({'id':i,'n':M[i][0],'p':M[i][1],'pop':g(i,'c_pop') or 0,**f,'k':sum(f.values()),'fl_ok':g(i,'fl_rep') is not None})
df=pd.DataFrame(rows)
pop_by_k=df.groupby('k')['pop'].sum().to_dict()
trip=df[df.k==3].sort_values('pop',ascending=False)
two=df[df.k==2]
# combos
combo={}
for _,x in df.iterrows():
    key='+'.join([c for c in TH if x[c]]) or 'none'; combo[key]=combo.get(key,0)+x['pop']
# correlations
HZ=[('ht_n30','Hot nights'),('pm_d55','Unhealthy air days'),('fl_rep','Land flooded 3+ times'),('tw_n','Night warming'),('ht_d45','Days above 45 °C')]
OUT=[('mpi_h','Multidimensionally poor'),('h_pcc','Consumption per person'),('n_stunt','Stunting'),('n_waste','Wasting'),('lit','Literacy'),('p_imr','Infant mortality'),('food','Food insecurity')]
C=[]
for hc,hl in HZ:
    row=[]
    for oc,ol in OUT:
        a=[(g(i,hc),g(i,oc)) for i in M if g(i,hc) is not None and g(i,oc) is not None and (V[str(i)][oc][1]>=25)]
        rho,p=spearmanr([x[0] for x in a],[x[1] for x in a]); row.append([round(rho,2),len(a),round(p,3)])
    C.append(row)
out={'th':TH,'popk':{int(k):int(v) for k,v in pop_by_k.items()},'tot':int(df['pop'].sum()),
     'trip':[[x.n,x.p,int(x.pop)] for x in trip.itertuples()],'combo':{k:int(v) for k,v in combo.items()},
     'corr':{'h':[h[1] for h in HZ],'hc':[h[0] for h in HZ],'o':[o[1] for o in OUT],'oc':[o[0] for o in OUT],'v':C}}
h=json.load(open('shumaar/heat.json')); h['hz']=out; json.dump(h,open('shumaar/heat.json','w'),separators=(',',':'))
dj['inds']['hz_n']={'label':'Climate hazards faced: hot nights, unhealthy air, repeat floods (0-3)','src':'Shumaar composite of satellite and model layers','theme':'Climate','hb':True,'rural':False,'noN':True,'tier':'model','unit':'hazards',
 'check':'Counts three hazards at fixed cut-offs: 10 or more hot nights a year (ERA5-Land, 2011-25), 150 or more unhealthy air days a year (CAMS rescaled to ACAG, 2021-25), and 2% or more of land flooded three or more times (Global Flood Database, 2000-18). Mountain districts have no flood value.',
 'orig':'Number of the three hazards above their cut-off in the district: hot nights (10+ a year above 30 °C), unhealthy air (150+ days a year above 55.5 µg/m³ PM2.5) and repeat floods (2%+ of land flooded three or more times).'}
for x in df.itertuples(): V.setdefault(str(x.id),{})['hz_n']=[int(x.k),99999]
json.dump(dj,open('shumaar/districts.json','w'),separators=(',',':'),ensure_ascii=False)
print(out['popk'],out['tot']); print(out['trip'][:12]); print(sorted(out['combo'].items(),key=lambda x:-x[1]))
for hl,row in zip(out['corr']['h'],C): print(hl,row)
