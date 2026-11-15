import json, re, numpy as np, pandas as pd
exec(open('build/places.py').read().split('def layer')[0])
R=json.load(open('build/lfs25_districts.json'))
FIXN={'DER GHAZI KHAN':'DERA GHAZI KHAN','D.I.KHAN':'DERA ISMAIL KHAN','BAHWALNAGAR':'BAHAWALNAGAR','KACHHI/BOLAN':'KACHHI','KECH/TURBAT':'KECH','SURAB':'SHAHEED SIKANDARABAD'}
kn=lambda v: k(FIXN.get(v['name'],v['name']))
byk={kn(v):v for v in R['dist'].values() if v.get('name')}
rbyk={kn(v):v for v in R['rdist'].values() if v.get('name')}
m=lookup(set(byk))
miss=[f['properties']['n'] for f in geo['features'] if str(f['id']) not in m]; print('mapped',len(m),'miss',len(miss),miss[:30])
SRC=("Labour Force Survey 2024-25 (Pakistan Bureau of Statistics), computed from microdata with survey weights. "
     "District from the sample frame code; divisional strata (incl. all of Balochistan) placed by census enumeration-block prefix learnt from LFS 2020-21. "
     "The survey is designed for provinces, so district figures are rough; shown where at least 100 people were interviewed for the measure.")
spec={'l_flfp':('flfp','Women 10+ in the labour force (working, or looking for and available for work).'),
 'l_unemp':('unemp','Unemployed (no work, looking and available) as % of the labour force, 10+.'),
 'l_youth':('youth','Unemployment rate among 15-24 year olds.'),
 'l_agri':('agri','Employed people whose main job is in agriculture, forestry or fishing (ISIC Rev.4 divisions 01-03).'),
 'l_wage':('wage','Mean monthly take-home pay of employees reporting a wage.'),
 'l_pens':('pens','Employees whose job provides an old-age pension.'),
 'l_gap':('gap',"Women's labour force participation rate per 100 of men's (10+)."),
 'lf_flfp':('flfp','Women 10+ in the labour force.'),
 'lf_unemp':('unemp','Unemployment rate, 10+.'),
 'lf_youth':('youthemp','Share of 15-24 year olds who are employed.'),
 'lf_manu':('manu','Employed people working in manufacturing (ISIC Rev.4 divisions 10-33).')}
cmp={}
for code,(key,desc) in spec.items():
    old={f:v[code][0] for f,v in D['vals'].items() if code in v}
    new={}
    for fid,kk in m.items():
        src=rbyk if code.startswith('l_') else byk
        if kk not in src: continue
        val,n=src[kk][key]
        if val is None or (isinstance(val,float) and np.isnan(val)) or n<100: 
            D['vals'].get(fid,{}).pop(code,None); continue
        D['vals'].setdefault(fid,{})[code]=[round(float(val),1 if key!='wage' else 0), int(n)]; new[fid]=val
    for fid in list(old):
        if fid not in new: D['vals'].get(fid,{}).pop(code,None)
    D['inds'][code].update(src='LFS 2024-25', orig=desc+' '+SRC)
    D['inds'][code].pop('noN',None); D['inds'][code]['rural']=code.startswith('l_')
    if code.startswith('l_'): D['inds'][code]['orig']='Rural areas only. '+D['inds'][code]['orig']
    PV={'Pakistan':'Pakistan','Punjab':'Punjab','Sindh':'Sindh','Khyber Pakhtunkhwa':'Khyber Pakhtunkhwa','Balochistan':'Balochistan'}
    D['prov'][code]={p:round((R['rprov'] if code.startswith('l_') else R['prov'])[p][key][0],2) for p in PV}
    c=[f for f in new if f in old]
    cmp[code]=(len(old),len(new),round(float(np.corrcoef([old[f] for f in c],[new[f] for f in c])[0,1]),3) if len(c)>5 else None, round(float(np.median([abs(old[f]-new[f]) for f in c])),2) if c else None)
# change in women's participation since 2020-21 (lf21_flfp layer already computed by us from LFS 2020-21 microdata)
n=0
for fid,v in D['vals'].items():
    if 'lf_flfp' in v and 'lf21_flfp' in v: v['lf_flfpch']=[round(v['lf_flfp'][0]-v['lf21_flfp'][0],1),v['lf_flfp'][1]]; n+=1
    else: v.pop('lf_flfpch',None)
D['inds']['lf_flfpch'].update(src='LFS 2020-21 to 2024-25',orig="Women's labour force participation (10+) in 2024-25 minus 2020-21, both from LFS microdata with survey weights. "+SRC)
D['inds']['lf_flfpch'].pop('noN',None)
D['prov']['lf_flfpch']={p:round(D['prov']['lf_flfp'][p]-D['prov']['lf21_flfp'][p],2) for p in D['prov']['lf_flfp'] if p in D['prov'].get('lf21_flfp',{})}
print('lf_flfpch',n)
for c,v in cmp.items(): print(c,'old n',v[0],'new n',v[1],'corr',v[2],'median abs diff',v[3])
json.dump(D,open(OUT+'districts.json','w'),separators=(',',':'),allow_nan=False)
