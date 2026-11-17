# City tifs (epoch/crop2017/built_last) -> app PNGs + stats json
import rasterio, numpy as np, json, os, math
from PIL import Image
from scipy import ndimage
SRC='cityraw'; OUT='shumaar/city'; os.makedirs(OUT,exist_ok=True)
# epoch colors on dark ground (oldest dim -> newest bright)
COL={1:(138,74,74),2:(184,92,60),3:(224,123,57),4:(255,169,77),5:(255,224,138)}
BG=(12,15,14); CROP=(26,36,28)
ENV=(127,212,193)
stats={}
for f in sorted(os.listdir(SRC)):
    if not f.endswith('.tif'): continue
    name=f[:-4]
    r=rasterio.open(f'{SRC}/{f}'); ep=r.read(1); crop=r.read(2); built=r.read(3)
    lat=(r.bounds.top+r.bounds.bottom)/2
    px=(30*0.0002694945852358565*111320*math.cos(math.radians(lat)))/1e6*30/30  # km2: 30m x 30m*cos? compute properly below
    # pixel ground size: dy = res_deg*111320 m ; dx = res_deg*111320*cos(lat)
    dy=r.res[0]*111320; dx=r.res[0]*111320*math.cos(math.radians(lat)); px=dx*dy/1e6
    cum={}
    for y,vals in [('1990',[1]),('2000',[1,2]),('2010',[1,2,3]),('2018',[1,2,3,4]),('latest',[1,2,3,4,5])]:
        cum[y]=round(float(np.isin(ep,vals).sum())*px,1)
    # connected envelope: close built mask, largest component near centre, fill holes
    m=built>0
    m2=ndimage.binary_closing(m,structure=np.ones((5,5)))  # ~150 m bridging
    m2=ndimage.binary_fill_holes(m2)
    lab,n=ndimage.label(m2)
    h,w=lab.shape; cy,cx=h//2,w//2
    win=lab[max(0,cy-100):cy+100,max(0,cx-100):cx+100]
    ids,cts=np.unique(win[win>0],return_counts=True)
    if len(ids)==0:
        sizes=ndimage.sum(np.ones_like(lab),lab,range(1,n+1)); core=int(np.argmax(sizes))+1
    else: core=int(ids[np.argmax(cts)])
    env=lab==core
    env_km2=round(float(env.sum())*px,1)
    built_in_env=round(float((m&env).sum())*px,1)
    # render
    img=np.zeros((h,w,3),np.uint8); img[:]=BG
    img[crop>0]=CROP
    for v,c in COL.items(): img[ep==v]=c
    im=Image.fromarray(img)
    scale=1100/w; nh=int(h*scale)
    im=im.resize((1100,nh),Image.LANCZOS)
    # outline drawn at display size so it stays crisp
    envs=np.array(Image.fromarray(env.astype(np.uint8)*255).resize((1100,nh),Image.NEAREST))>127
    edge=envs^ndimage.binary_erosion(envs,np.ones((3,3)))
    edge=ndimage.binary_dilation(edge,np.ones((2,2)))
    a=np.array(im); a[edge]=(77,227,184); im=Image.fromarray(a)
    im=im.quantize(48,dither=Image.Dither.NONE)
    im.save(f'{OUT}/{name.lower()}.png',optimize=True)
    stats[name]={'km2':cum,'env':env_km2,'env_built':built_in_env,'px_w_km':round(dx*w/1000,1)}
    print(name,cum,'env',env_km2,'built in env',built_in_env)
json.dump(stats,open('build/cities_stats.json','w'),indent=1)
