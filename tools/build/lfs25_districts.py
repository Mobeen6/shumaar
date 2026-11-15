# LFS 2024-25 microdata -> district labour indicators (survey weights).
# District: PCode[:3] when the stratum is a district (3rd digit != 0), named by the S4C16 value labels;
# divisional strata (3rd digit 0, incl. all Balochistan) are placed by census enumeration-block prefix (EBCode[:3]),
# learnt from LFS 2020-21 where every record carries a district name.
import pandas as pd, numpy as np, json, re
F25='raw/lfs25/LFS 2024-25.sav web.dta'; F21='raw/lfs21/LFS2020-21.dta'
rd=pd.io.stata.StataReader(F25); lab={int(k):v.strip().upper() for k,v in rd.value_labels()['S4C16'].items() if k<900}
cols=['PCode','EBCode','Province','Region','Weights','S4C5','S4C6','S5C1','S5C2','S5C3','S5C4','S5C11','S5C13','S7C43','S7C61','S9C1','S9C6']
d=pd.read_stata(F25,columns=cols,convert_categoricals=False)
nm=lambda s: re.sub(r'[^A-Z]','',str(s).upper())
code_by_name={nm(v):k for k,v in lab.items()}
fix={'DERAGHAZIKHAN':281,'DERAISMAILKHAN':171,'KAMBARSHAHDADKOT':315,'TANDOMUHAMMADKHAN':335,'KACHHI':451,'KECH':471,'SHAHEEDSIKANDARABAD':466,'BAHAWALNAGAR':292}
e21=pd.read_stata(F21,columns=['Province','EBCode','District'],convert_categoricals=False).dropna()
e21['eb3']=e21.EBCode.astype('int64').astype(str).str[:3]; e21['c']=e21.District.map(lambda x: code_by_name.get(nm(x),fix.get(nm(x))))
g=e21.dropna(subset=['c']).groupby(['Province','eb3']).c.agg(lambda s: s.iloc[0] if s.nunique()==1 else np.nan).dropna()
ebx={(int(p),e):int(c) for (p,e),c in g.items()}
d['p3']=d.PCode.astype('int64').astype(str).str[:3]
isdiv=d.p3.str[2]=='0'
d['dc']=np.nan
d.loc[~isdiv,'dc']=pd.to_numeric(d.loc[~isdiv,'p3'])
eb3=d.EBCode.fillna(0).astype('int64').astype(str).str[:3]
d.loc[isdiv,'dc']=pd.Series([ebx.get((int(p),e),np.nan) for p,e in zip(d.loc[isdiv,'Province'],eb3[isdiv])],index=d.index[isdiv],dtype=float)
print('rows',len(d),'placed',d.dc.notna().mean().round(3),'districts',d.dc.nunique())
a=d[d.S4C6>=10].copy(); w='Weights'
E=(a.S5C1==1)|(a.S5C2==1)|(a.S5C3==1)|(a.S5C4==1)
U=~E&(a.S9C1==1)&(a.S9C6==1)
a['E']=E; a['U']=U; a['L']=E|U
ind=pd.to_numeric(a.S5C13,errors='coerce'); div=ind//100   # 4-digit ISIC Rev.4 class stored without its leading zero
a['div']=div
def wm(x,y,m=None):
    m=np.ones(len(x),bool) if m is None else m
    ww=x.loc[m,w]; return float((ww*y[m]).sum()/ww.sum()*100) if ww.sum()>0 else np.nan
def stats(s):
    f=s.S4C5==2; mm=s.S4C5==1; y=s.S4C6.between(15,24)
    o={}
    o['flfp']=(wm(s,s.L,f), int(f.sum()))
    mlfp=wm(s,s.L,mm); o['gap']=(o['flfp'][0]/mlfp*100 if mlfp else np.nan, int(len(s)))
    o['unemp']=(wm(s,s.U,s.L), int(s.L.sum()))
    o['youth']=(wm(s,s.U,s.L&y), int((s.L&y).sum()))
    o['youthemp']=(wm(s,s.E,y), int(y.sum()))
    o['agri']=(wm(s,s['div'].between(1,3),s.E), int(s.E.sum()))
    o['manu']=(wm(s,s['div'].between(10,33),s.E), int(s.E.sum()))
    emp=s.E&(s.S5C11==3); wg=pd.to_numeric(s.S7C43,errors='coerce'); ok=emp&(wg>0)
    o['wage']=(float((s.loc[ok,w]*wg[ok]).sum()/s.loc[ok,w].sum()) if ok.sum() else np.nan, int(ok.sum()))
    o['pens']=(wm(s,(s.S7C61==1),emp), int(emp.sum()))
    return o
PN={1:'Khyber Pakhtunkhwa',2:'Punjab',3:'Sindh',4:'Balochistan'}
prov={'Pakistan':stats(a)}; prov.update({n:stats(a[a.Province==p]) for p,n in PN.items()})
dist={int(c):dict(stats(s),name=lab.get(int(c))) for c,s in a.dropna(subset=['dc']).groupby('dc')}
rur=a[a.Region==1]   # Region 1 = rural
rdist={int(c):dict(stats(s),name=lab.get(int(c))) for c,s in rur.dropna(subset=['dc']).groupby('dc')}
rprov={'Pakistan':stats(rur)}; rprov.update({n:stats(rur[rur.Province==p]) for p,n in PN.items()})
json.dump({'prov':prov,'dist':dist,'rprov':rprov,'rdist':rdist},open('build/lfs25_districts.json','w'),default=float)
print(pd.DataFrame({k:{i:round(v[0],2) for i,v in x.items()} for k,x in prov.items()}).to_string())
