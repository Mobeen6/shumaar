import json, re, numpy as np
exec(open('build/places.py').read().split('def layer')[0])
B=json.load(open('beoe/beoe.json')); S={int(k):v for k,v in json.load(open('beoe/skill.json')).items()}
tot=lambda y: sum(S[y][:5])
for p in ['shumaar/migration.json','repo/migration.json']:
    M=json.load(open(p))
    yrs=list(range(2000,2026)); names=['HighlyQualified','HighlySkilled','Skilled','SemiSkilled','UnSkilled']
    M['skill']={'yrs':yrs,'rows':[[n,[S[y][i] for y in yrs]] for i,n in enumerate(names)]}
    c={k:v for k,v in B['country'].items() if k!='Others'}
    NM={'U.A.E':'United Arab Emirates','U.K':'United Kingdom','U.S.A':'United States'}
    for y in ['2015','2024']:
        M['dest'][y]=[[NM.get(k,k),v[y]] for k,v in sorted(c.items(),key=lambda kv:-kv[1][y])[:10]]
    G=['Saudi Arabia','U.A.E','Oman','Qatar','Bahrain','Kuwait']
    M['gshare']={str(y):round(sum(B['country'][g][str(y)] for g in G)/tot(y)*100,1) for y in range(2014,2026)}
    M['occ']=[[k,v['2024']] for k,v in sorted(B['category'].items(),key=lambda kv:-kv[1]['2024'])[:14]]
    json.dump(M,open(p,'w'),separators=(',',':'),ensure_ascii=False)
# districts
FIX={'bahwalnagar':'bahawalnagar','bahwalpur':'bahawalpur','bhakar':'bhakkar','bajour':'bajaur','bonair':'buner','charsada':'charsadda','ghanchi':'ghanche','ghizar':'ghizer','gowadar':'gwadar','haripurhazara':'haripur','layya':'leiah','matari':'matiari','mehmand':'mohmand','noshki':'nushki','noushehroferoze':'naushahroferoze','sudnuti':'sudhnoti','tobateksing':'tobateksingh','turbat':'kech','bolan':'kachhi','deraismailkhan':'dikhan','tandomuhammadkhan':'tandomuhammadkhan','kambar':'kambarshahdadkot','shahdadkot':'kambarshahdadkot'}
dk={}
for n,v in B['district'].items():
    kk=k(n); kk=FIX.get(kk,kk)
    if kk in dk: dk[kk]={y:dk[kk][y]+v[y] for y in v}
    else: dk[kk]=v
m=lookup(set(dk)); miss=[f['properties']['n'] for f in geo['features'] if str(f['id']) not in m]
print('mapped',len(m),'miss',len(miss),miss)
print('unused',sorted(set(dk)-set(m.values()))[:60])
used={}
for fid,kk in m.items(): used.setdefault(kk,[]).append(fid)
old={f:v.get('mg_emig',[None])[0] for f,v in D['vals'].items()}
n=0; top=[]
for kk,fids in used.items():
    v=dk[kk]; e=sum(v[str(y)] for y in range(2020,2025)); t=sum(v[str(y)] for y in range(2014,2026))
    pop=sum(D['vals'].get(f,{}).get('c_pop',[0])[0] for f in fids)
    if len(fids)>1: print('shared',kk,len(fids))
    for f in fids:
        D['vals'].setdefault(f,{})['mg_tot']=[t,0]
        if pop: D['vals'][f]['mg_emig']=[round(e/pop*1000,1),0]; n+=1
    if pop and len(fids)==1:
        pr=next(g['properties']['p'] for g in geo['features'] if str(g['id'])==fids[0])
        top.append([next(g['properties']['n'] for g in geo['features'] if str(g['id'])==fids[0]),pr,round(e/pop*1000,1),e])
for f,v in D['vals'].items():
    if f not in m: v.pop('mg_emig',None); v.pop('mg_tot',None)
D['inds']['mg_emig']['orig']="Bureau of Emigration & Overseas Employment, workers registered for employment abroad by district of origin, 2020-2024 (through BE&OE and OEC), per 1,000 residents (Census 2023). Districts as in the Bureau's list; districts it does not list separately are combined with their parent district."
D['inds']['mg_tot'].update(label='Emigrants registered, 2014-2025',orig="Bureau of Emigration & Overseas Employment, workers registered for employment abroad by district of origin, 2014-2025 (through BE&OE and OEC).")
c=[f for f,v in D['vals'].items() if 'mg_emig' in v and old.get(f)]
print('layers',n,'corr old/new',round(float(np.corrcoef([old[f] for f in c],[D['vals'][f]['mg_emig'][0] for f in c])[0,1]),3), 'n',len(c))
top.sort(key=lambda r:-r[2])
for p in ['shumaar/migration.json','repo/migration.json']:
    M=json.load(open(p)); print('old top',M['topd'][:5]); M['topd']=top[:15]; json.dump(M,open(p,'w'),separators=(',',':'),ensure_ascii=False)
print('new top',top[:8])
json.dump(D,open(OUT+'districts.json','w'),separators=(',',':'),allow_nan=False)
