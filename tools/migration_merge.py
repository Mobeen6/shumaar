"""Update remittance parts of migration.json from SBP's own file (via sbp.json)."""
import json
S=json.load(open('sbp.json'))['s']; M=json.load(open('migration.json'))
tot=S['rem']; G=['Saudi Arabia','UAE','UK','USA','Other Gulf','EU']
def fy(m): y,mo=map(int,m.split('-')); return y+(mo>=7)
by={}
for m,v in tot.items():
    f=fy(m); by.setdefault(f,{'n':0,'tot':0,**{g:0 for g in G}}); by[f]['n']+=1; by[f]['tot']+=v
    for g in G: by[f][g]+=S['rem_'+g].get(m,0)
rows=[]
for f in sorted(by):
    b=by[f]
    if f<2011 or b['n']<12: continue
    r={'fy':f,'tot':round(b['tot']/1e3,2),**{g:round(b[g]/1e3,2) for g in G}}; r['Other']=round(r['tot']-sum(r[g] for g in G),2); rows.append(r)
M['rem']=rows
ms=sorted(m for m in tot if m>='2016-01'); M['monthly']={'m':ms,'v':[round(tot[m],1) for m in ms]}
json.dump(M,open('migration.json','w'),separators=(',',':'))
print(rows[-2:], ms[-1])
