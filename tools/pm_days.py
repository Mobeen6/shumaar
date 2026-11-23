"""Days of unhealthy air by district from CAMS daily PM2.5 (geo/shumaar_gee_pm_daily.js), rescaled to ACAG/WashU annual means.
2017-2022: each district-year scaled so its annual mean equals ACAG's; 2023 on: the district's mean 2020-2022 factor."""
import pandas as pd,numpy as np,json,shapefile
r=shapefile.Reader('geo/shp/shumaar_districts_shp.shp'); M={x[0]:(x[1],x[2]) for x in r.records()}
d=pd.read_csv('build/pm_daily.csv'); d['y']=d.d.str[:4].astype(int)
a=pd.read_csv('build/acag.csv'); yc={int(c.split('_')[3][:4]):c for c in a.columns if c.startswith('V6')}
A=a.set_index('id')[[yc[y] for y in range(2017,2023)]]; A.columns=range(2017,2023)
C=d.groupby(['id','y']).pm.mean().unstack()
K=(A/C[list(range(2017,2023))])
kl=K[[2020,2021,2022]].mean(axis=1)
for y in range(2023,2027): K[y]=kl
d['k']=[K.at[i,y] for i,y in zip(d.id,d.y)]; d['pc']=d.pm*d.k
T={'neqs':35,'us':55.5,'who':15}
for t,v in T.items(): d[t]=d.pc>v
last=d.d.max()
cnt=d.groupby(['id','y'])[list(T)].sum().astype(int)
nd=d.groupby(['id','y']).size()
if __name__=='__main__':
    for nm in ['Lahore','Faisalabad','East Karachi','Peshawar','Islamabad','Quetta','Gilgit']:
        i=[i for i,(n,p) in M.items() if n==nm][0]; print(nm, cnt.loc[i].T.to_dict('list') if False else cnt.loc[i]['neqs'].to_dict(), '| US unhealthy', cnt.loc[i]['us'].to_dict())
    print('last day',last)

def build():
    dj=json.load(open('shumaar/districts.json'))
    pop={int(f):v['c_pop'][0] for f,v in dj['vals'].items() if 'c_pop' in v}
    d['m']=d.d.str[5:7].astype(int)
    yrs=list(range(2017,2027)); out={'years':yrs,'last':last,'d':{}}
    av=cnt.loc[(slice(None),slice(2021,2025)),:].groupby(level=0).mean()
    for i in sorted(M):
        sub=d[d.id==i]; mc={t:sub.groupby(['y','m'])[t].sum().unstack().reindex(index=yrs,columns=range(1,13)) for t in ('neqs','us')}
        out['d'][str(i)]={'n':M[i][0],'p':M[i][1],'avg':[round(av.at[i,t]) for t in ('who','neqs','us')],
          'neqs':[[None if pd.isna(x) else int(x) for x in row] for row in mc['neqs'].values.tolist()],
          'us':[[None if pd.isna(x) else int(x) for x in row] for row in mc['us'].values.tolist()]}
    # province / national population-weighted averages
    P={}; ids=[i for i in M if i in pop]
    for reg in ['Pakistan','Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan','Islamabad ICT']:
        s=[i for i in ids if reg=='Pakistan' or M[i][1]==reg]; w=np.array([pop[i] for i in s])
        if not s: continue
        P[reg]=[round(float(np.average([av.at[i,t] for i in s],weights=w))) for t in ('who','neqs','us')]
    out['prov']=P
    json.dump(out,open('shumaar/pmdays.json','w'),separators=(',',':'))
    base={'src':'CAMS daily PM2.5 rescaled to ACAG, 2021-25','theme':'Climate','hb':True,'rural':False,'noN':True,'tier':'model',
      'check':'Copernicus CAMS daily PM2.5 (ECMWF, about 40 km), each district rescaled so its annual mean matches ACAG/WashU satellite PM2.5 (2017-2022). Counts are averaged over 2021-2025 because CAMS model upgrades shift single years.'}
    dj['inds']['pm_d35']={**base,'label':'Days a year above Pakistan\'s 24-hour PM2.5 standard (35 µg/m³), 2021-25 average','unit':'days a year','orig':'Days per year on which the district-average PM2.5 exceeded 35 µg/m³, the 24-hour limit in Pakistan\'s National Environmental Quality Standards. Average of 2021-2025.'}
    dj['inds']['pm_d55']={**base,'label':'Unhealthy air days a year (PM2.5 above 55.5 µg/m³), 2021-25 average','unit':'days a year','orig':'Days per year on which the district-average PM2.5 exceeded 55.5 µg/m³, the level the US Air Quality Index calls unhealthy for everyone. Average of 2021-2025.'}
    for i in M:
        v=dj['vals'].setdefault(str(i),{}); v['pm_d35']=[round(av.at[i,'neqs']),99999]; v['pm_d55']=[round(av.at[i,'us']),99999]
    dj['prov']['pm_d35']={k:v[1] for k,v in P.items()}; dj['prov']['pm_d55']={k:v[2] for k,v in P.items()}
    json.dump(dj,open('shumaar/districts.json','w'),separators=(',',':'),ensure_ascii=False)
    print(P); print(sorted([(round(av.at[i,'us']),M[i][0]) for i in M])[-10:])
build()
