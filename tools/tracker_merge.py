"""Update tracker.json series that come from SBP's own files (sbp.json). Other series are left as they are."""
import json
S=json.load(open('sbp.json'))['s']; T=json.load(open('tracker.json'))
MAP={'rem':'rem','ca':'ca','x':'x','m':'m','res':'res','usd':'usd'}
for k,sk in MAP.items():
    s={m:v for m,v in S[sk].items() if m>='2021-01' and v is not None}
    T[k]['m']=sorted(s); T[k]['v']=[round(float(s[m]),3) for m in T[k]['m']]; T[k]['src']='SBP'
json.dump(T,open('tracker.json','w'),separators=(',',':'))
print({k:T[k]['m'][-1] for k in MAP})
