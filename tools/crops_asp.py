"""National and provincial crop area/production from MNFSR Agricultural Statistics of Pakistan 2024-25 (text via pdftotext)."""
import re, json
L=open('asp.txt').read().split('\n')
CROPS={'Wheat':'WHEAT','Rice':'RICE','Maize':'MAIZE','Sugarcane':'SUGARCANE','Cotton':'COTTON'}
row=re.compile(r'^\s*(\d{4}-\d{2})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$')
out={}
for cr,head in CROPS.items():
    st=next(i for i in range(len(L)-1) if re.match(r'^\s*Table[- ]\d+\s*$',L[i]) and L[i+1].strip()==head)
    sec=None; A={}; P={}; prov={}
    for l in L[st+2:st+120]:
        if re.search(r'\(\s*Area',l,re.I): sec='a'; continue
        if re.search(r'\(\s*(Production|Cotton Lint)',l,re.I): sec='p'; continue
        if re.search(r'\(Yield|Contd|Table',l,re.I) and sec=='p' and P: break
        m=row.match(l)
        if m and sec:
            vals=[float(x) for x in m.groups()[1:]]
            (A if sec=='a' else P)[m[1]]=vals
    fys=sorted(set(A)&set(P))
    out[cr]={'fy':fys,'a':[A[f][4] for f in fys],'p':[P[f][4] for f in fys],'y':[round(P[f][4]/A[f][4],3) if A[f][4] else None for f in fys],
             'prov':dict(zip(['Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan'],P[fys[-1]][:4]))}
    print(cr,fys[0],fys[-1],out[cr]['a'][-1],out[cr]['p'][-1],out[cr]['prov'])
json.dump(out,open('build/crops_asp.json','w'))
