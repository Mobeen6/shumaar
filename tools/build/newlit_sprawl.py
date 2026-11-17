import rasterio,numpy as np,json,csv,math
from scipy import ndimage
# ---- newly lit since 2012 (1 km annual stack) ----
r=rasterio.open('nl2/annual.tif'); a=r.read().astype(np.float32)/10
ids=np.load('nl2/ids.npy'); g=json.load(open('repo/districts.geojson')); F=g['features']
early=a[0:2].mean(0); late=(a[13]+a[14])/2   # 2012-13 vs 2025+last12m
lit=late>1.0; new=lit&(early<0.5)
T=r.transform; lat=T.f+T.e*(np.arange(r.height)+.5)
pa=(abs(T.a)*111.32*np.cos(np.radians(lat)))*(abs(T.e)*110.57); PA=np.broadcast_to(pa[:,None],ids.shape)
n=len(F)+1
litA=np.bincount(ids.ravel(),weights=(lit*PA).ravel(),minlength=n)
newA=np.bincount(ids.ravel(),weights=(new*PA).ravel(),minlength=n)
print('national lit km2',round(litA[1:].sum()),'newly lit',round(newA[1:].sum()),'share',round(newA[1:].sum()/litA[1:].sum()*100,1))
NL={}
import collections; pv=collections.defaultdict(lambda:[0,0])
for k,f in enumerate(F,1):
    d=str(f['id']); share=round(newA[k]/litA[k]*100,1) if litA[k]>=20 else None
    NL[d]=(share,round(newA[k]))
    p=f['properties']['p']; pv[p][0]+=newA[k]; pv[p][1]+=litA[k]
provNL={p:round(a/b*100,1) for p,(a,b) in pv.items() if p in('Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan') and b>0}
provNL['Pakistan']=round(newA[1:].sum()/litA[1:].sum()*100,1)
top=sorted(((v[1],v[0],F[int(k)]['properties']['n']) for k,v in NL.items() if v[0] is not None),reverse=True)[:8]
print('most new lit km2:',[(t[2],t[0],t[1]) for t in top])
# ---- built-up per person (district) ----
R={r_['id']:float(r_['built_last_km2']) for r_ in csv.DictReader(open('build/farmland.csv'))}
D0=json.load(open('shumaar/districts.json'))
BP={}
for d,b in R.items():
    pop=(D0['vals'].get(d,{}).get('c_pop') or [None])[0]
    if pop and pop>0: BP[d]=round(b*1e6/(pop*1e6)*1,1) if False else round(b/pop*1000,1)  # km2 per 1000 -> m2pp = *1000
# m2 per person = built_km2*1e6 / pop_m ... c_pop unit? check later
json.dump({'NL':NL,'provNL':provNL,'BP':BP},open('build/newlit_tmp.json','w'))
# ---- city infill: share of post-2010 growth outside the 2000 envelope ----
out={}
for name in ['Karachi','Lahore','Faisalabad','Rawalpindi_Islamabad','Gujranwala','Peshawar','Multan','Hyderabad','Quetta','Bahawalpur','Sargodha','Sialkot','Sukkur','Larkana','Sheikhupura','Rahim_Yar_Khan','Jhang','Dera_Ghazi_Khan','Gujrat','Mardan']:
    rr=rasterio.open(f'cityraw/{name}.tif'); ep=rr.read(1)
    old=np.isin(ep,[1,2])
    env=ndimage.binary_fill_holes(ndimage.binary_closing(old,np.ones((5,5))))
    newb=np.isin(ep,[4,5])
    tot=newb.sum()
    out[name.lower()]=round(float((newb&~env).sum())/tot*100) if tot else None
print('outside-2000 share:',sorted(out.items(),key=lambda x:-x[1]))
json.dump(out,open('build/infill.json','w'))
