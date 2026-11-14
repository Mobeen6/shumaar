# Punjab Crop Reporting Service final estimates -> district production and yield (current year = first TOTAL column)
import re,sys,json
def tables(path):
    L=open(path).read().split('\n'); T={};cur=None
    for i,l in enumerate(L):
        m=re.search(r'ESTIMATE OF (.+?) CROP',l)
        if m:
            unit=' '.join(L[i:i+4]); cur=(m.group(1).strip(),re.search(r'\((.*?)\)',unit).group(1) if re.search(r'\((.*?)\)',unit) else '')
            T.setdefault(cur,{}); continue
        if not cur: continue
        p=re.split(r'\s{2,}',l.strip())
        if len(p)<2 or p[0].isupper() or not re.match(r'[A-Z][a-zA-Z .]+$',p[0]): continue
        nums=[float(x) for x in p[1:] if re.fullmatch(r'-?[\d.]+',x)]
        if nums: T[cur][p[0]]=nums
    return T
out={}
for f in sys.argv[1:]:
    for (crop,unit),rows in tables(f).items(): out[f'{crop}|{unit}']=rows
json.dump(out,open('build/crs_punjab.json','w'))
for k in out: print(k,len(out[k]))
