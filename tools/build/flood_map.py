import rasterio,numpy as np
from PIL import Image,ImageDraw,ImageFont
r=rasterio.open('floodraw/fr.tif'); fl,b22,nb=r.read()
f=12  # 30 m -> 360 m display cells
H=(fl.shape[0]//f)*f; W=(fl.shape[1]//f)*f
def pool(a,fn):
    a=a[:H,:W].reshape(H//f,f,W//f,f); return fn(a,axis=(1,3))
flm=pool(fl,np.mean); b22m=pool(b22,np.max); nbin=pool(nb*fl,np.max); nbout=pool(nb*(1-fl),np.max)
img=np.zeros(flm.shape+(3,),np.uint8); img[:]=(14,18,17)
w=flm>0.25; img[w]=(38,86,128); img[flm>0.6]=(52,120,172)
img[b22m>0]=(150,150,140)
img[nbout>0]=(240,214,140)
img[nbin>0]=(255,92,52)
im=Image.fromarray(img); sc=1100/im.width; im=im.resize((1100,int(im.height*sc)),Image.NEAREST)
d=ImageDraw.Draw(im)
font=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',17)
T=r.transform
def xy(lon,lat):
    c,rr=~T*(lon,lat); return c/f*sc, rr/f*sc
for n,lon,lat in [('Larkana',68.21,27.56),('Sukkur',68.86,27.71),('Jacobabad',68.44,28.28),('Shikarpur',68.64,27.96),('Dadu',67.78,26.73),('Khairpur',68.76,27.53),('Nawabshah',68.41,26.24),('Kambar',67.99,27.59),('Mehar',67.82,27.18),('Ghotki',69.32,28.01),('Moro',68.0,26.66)]:
    x,y=xy(lon,lat)
    if 0<x<1100 and 0<y<im.height:
        d.ellipse([x-3,y-3,x+3,y+3],fill=(255,255,255))
        d.text((x+7,y-11),n,font=font,fill=(255,255,255),stroke_width=3,stroke_fill=(14,18,17))
im=im.quantize(32,dither=Image.Dither.NONE)
im.save('shumaar/city/flood_sindh.png',optimize=True)
print(im.size)
