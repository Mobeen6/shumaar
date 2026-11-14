import urllib.request,os
os.makedirs('data_raw/real',exist_ok=True)
H={'Accept':'*/*','User-Agent':'Mozilla/5.0 (X11; Linux x86_64)'}
for tag,u in [('2021feb','https://www.sbp.org.pk/ecodata/kibor/2021/Feb/index.asp'),('2026oct','https://www.sbp.org.pk/ecodata/kibor/2026/Oct/index.asp'),
              ('2024may','https://www.sbp.org.pk/ecodata/kibor/2024/May/index.asp'),('index','https://www.sbp.org.pk/ecodata/kibor_index.asp')]:
    try: b=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60).read()
    except Exception as e: b=str(e).encode()
    open(f'data_raw/real/kibor_idx_{tag}.html','wb').write(b)
