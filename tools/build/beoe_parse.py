import re,json,sys
YRS=['pre']+list(range(2014,2019))+[(y,k) for y in range(2019,2027) for k in ('be','oec','tot')]+['TOTAL']
def parse(fn):
    out={}; prev=''
    for l in open(fn).read().split('\n'):
        t=re.match(r'\s*([A-Za-z][A-Za-z .()\'-]+?)\s*$',l)
        if t: prev=t.group(1); continue
        m=re.match(r'\s*(?:\d+\s+)?([A-Za-z][A-Za-z .,&/()\'-]*?)\s+((?:-?\d+\s+){29,}-?\d+)\s*$',l)
        if not m: continue
        nums=[int(x) for x in m.group(2).split()]
        if len(nums)!=31: print('skip',fn,m.group(1),len(nums),file=sys.stderr); continue
        r={}
        for k,v in zip(YRS,nums):
            if k=='pre': r['pre']=v
            elif k=='TOTAL': r['total']=v
            elif isinstance(k,int): r[str(k)]=v
            elif k[1]=='tot': r[str(k[0])]=v
        nm=m.group(1).strip()
        if nm in ('Agency','Khan') or nm.endswith(')') and '(' not in nm: nm=prev+' '+nm
        out[nm]=r
    return out
R={f:parse(f'{f}.txt') for f in ['district','country','category']}
json.dump(R,open('beoe.json','w'))
for f,v in R.items(): print(f,len(v),list(v)[:3])
