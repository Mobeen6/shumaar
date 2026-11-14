# Rebuild energy.json fuel / sys / idle from NEPRA State of Industry 2025, Tables 4, 5, 7, 8
import json,sys
P=json.load(open('build/plants25.json'))
order=["Hydro","Coal","Imported LNG","Local gas","Furnace oil","Nuclear","Wind","Solar","Bagasse"]
fix={'Libertv Power Tech.':'Liberty Power Tech','Fauii Kabirwala':'Fauji Kabirwala','Kohinoor EnerS!Y':'Kohinoor Energy',
 'Sannhire Electric':'Sapphire Electric','Puniab Thermal Power':'Punjab Thermal Power','Luckv Electric Power':'Lucky Electric Power',
 'SITE GTPS-11':'SITE GTPS-II (KE)','Korangi Town GTPS-11':'Korangi Town GTPS-II (KE)','Korangi CCPP':'Korangi CCPP (KE)',
 'Bin Qasim TPS-1':'Bin Qasim TPS-I (KE)','KAPCO':'Kot Addu Power Company','Attock Gen.':'Attock Gen'}
fuel=[]
for g in order:
    ps=[p for p in P if p['f']==g]
    mw=[round(sum(p['mw'][i] for p in ps)) for i in range(5)]
    gwh=[round(sum(p['gwh'][i] for p in ps)) for i in range(5)]
    fuel.append({'g':g,'mw':mw,'gwh':gwh,'cf':[round(gwh[i]/(mw[i]*8.76)*100,1) if mw[i] else None for i in range(5)]})
L=[]
for p in P:
    mw=p['mw'][4]
    if mw<100: continue
    cf=p['gwh'][4]/(mw*8.76)*100
    if cf<7: L.append([fix.get(p['n'],p['n']),p['f'],int(mw),int(p['mw'][5]) if len(p['mw'])>5 and p['mw'][5] else int(mw),round(p['gwh'][4],1),round(cf,1)])
L.sort(key=lambda r:(r[5],-r[2]))
for path in sys.argv[1:]:
    E=json.load(open(path))
    E['pfys']=['2020-21','2021-22','2022-23','2023-24','2024-25']
    E['fuel']=fuel
    E['sys']={'mw':[39772,43775,45738,45888,41121],'gwh':[143588,154056,138539,137078,135079]}  # Tables 4 and 7, whole country
    E['idle']=L
    json.dump(E,open(path,'w'),separators=(',',':'),ensure_ascii=False)
print(json.dumps(fuel)); print(L)
