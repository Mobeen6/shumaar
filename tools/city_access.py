"""Travel time to the nearest city of 50,000+ (MAP accessibility to cities 2015, WorldPop 2020 weights)."""
import json,pandas as pd,numpy as np
from scipy.stats import spearmanr
c=pd.read_csv('build/city_access.csv').set_index('id')
c['min']=c.popmin/c['pop']
for k in ('60','120','180'): c['s'+k]=np.minimum(100,100*c['pop'+k]/c['pop'])
dj=json.load(open('shumaar/districts.json')); V=dj['vals']
base={'src':'Malaria Atlas Project 2015; WorldPop 2020','theme':'Infrastructure','rural':False,'noN':True,'tier':'model',
 'check':'Modelled travel time (Weiss et al. 2018, Nature) to the nearest urban centre of 50,000+ people by the fastest mode, weighted by WorldPop 2020 population. Road network as of 2015; newer motorways are not reflected.'}
dj['inds']['ca_min']={**base,'label':'Average travel time to the nearest city, minutes','unit':'minutes','hb':True,'orig':'Population-weighted average travel time from where people live to the nearest town or city of 50,000+ people.'}
dj['inds']['ca_60']={**base,'label':'People more than an hour from a city, %','unit':'% of people','hb':True,'orig':'Share of the district\'s people living more than 60 minutes\' travel from the nearest town or city of 50,000+.'}
dj['inds']['ca_120']={**base,'label':'People more than two hours from a city, %','unit':'% of people','hb':True,'orig':'Share of the district\'s people living more than 120 minutes\' travel from the nearest town or city of 50,000+.'}
for i,r in c.iterrows():
    v=V.setdefault(str(i),{}); v['ca_min']=[round(r['min']),99999]; v['ca_60']=[round(r.s60,1),99999]; v['ca_120']=[round(r.s120,1),99999]
P={}
for reg in ['Pakistan','Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan','Islamabad ICT','Gilgit-Baltistan','Azad Jammu & Kashmir']:
    s=c if reg=='Pakistan' else c[c.p==reg]
    P[reg]=[round(s.popmin.sum()/s['pop'].sum()),min(100.0,round(100*s.pop60.sum()/s['pop'].sum(),1)),min(100.0,round(100*s.pop120.sum()/s['pop'].sum(),1)),round(s.pop60.sum()/1e6,1)]
for k,j in (('ca_min',0),('ca_60',1),('ca_120',2)): dj['prov'][k]={r:P[r][j] for r in P}
g=lambda i,k: V.get(str(i),{}).get(k,[None,0])
corr={}
for oc in ['mpi_h','h_pcc','n_stunt','lit','imm','p_imr']:
    a=[(g(i,'ca_min')[0],g(i,oc)[0]) for i in c.index if g(i,oc)[0] is not None and g(i,oc)[1]>=25]
    corr[oc]=[round(spearmanr(*zip(*a))[0],2),len(a)]
json.dump(dj,open('shumaar/districts.json','w'),separators=(',',':'),ensure_ascii=False)
top=c.sort_values('pop60',ascending=False).head(12).rename(columns={'pop':'pp'})
out={'prov':P,'top':[[r.n,r.p,round(r.pop60/1e3),round(r.s60)] for r in top.itertuples()],'corr':corr}
h=json.load(open('shumaar/heat.json')); h['ca']=out; json.dump(h,open('shumaar/heat.json','w'),separators=(',',':'))
print(P); print(out['top'][:8]); print(corr)
