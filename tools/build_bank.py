import json, sys, re
S, W = sys.argv[1], sys.argv[2]
imo=json.load(open(f'{S}/imo.json',encoding='utf-8')); apmo=json.load(open(f'{S}/apmo.json',encoding='utf-8'))
def group(L):
    g={}
    for x in L: g.setdefault(str(x['year']),[]).append(x['statement_raw'])
    return g
amc=[]
p=[f'{y} AMC 8' for y in range(1999,2027) if y!=2021]
amc.append({'name':'AMC 8','span':'1999–2026，共 %d 場'%len(p),'note':'沒有標為 2021 年的場次（考期改到 1 月，待核對）。前身 AJHSME 1985–1998 未列入。','papers':p})
p=[]
for y in range(2000,2026):
    for lv in ('10','12'):
        if y<2002: p.append(f'{y} AMC {lv}')
        elif y==2021: p += [f'2021 AMC {lv}A', f'2021 AMC {lv}B', f'2021 Fall AMC {lv}A', f'2021 Fall AMC {lv}B']
        else: p += [f'{y} AMC {lv}A', f'{y} AMC {lv}B']
amc.append({'name':'AMC 10／12','span':'2000–2025，共 %d 卷'%len(p),'note':'場次依記憶列出，尚未逐場核對。2000–2001 只有一場；2002 起分 A、B 卷；2021 有春季與秋季兩輪。2026 年 11 月場次尚未核對是否已公布。前身 AHSME 1950–1999 未列入。','papers':p})
p=[f'{y} AIME' for y in range(1983,2000)]+[f'{y} AIME {k}' for y in range(2000,2027) for k in ('I','II')]
amc.append({'name':'AIME','span':'1983–2026，共 %d 卷'%len(p),'note':'1983–1999 一年一卷，2000 起分 I、II 卷。','papers':p})
json.dump(amc,open(f'{W}/data/amc_index.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
data=json.dumps({'IMO':group(imo),'APMO':group(apmo),'AMC':amc},ensure_ascii=False,separators=(',',':')).replace('</','<\/')
h=open(f'{W}/math-map.html',encoding='utf-8').read()
h=re.sub(r'<script type="application/json" id="bank-data">.*?</script>\n','',h,flags=re.S)
i=h.index('<!-- ============ UNIT CONTENT ============ -->')
h=h[:i]+'<script type="application/json" id="bank-data">'+data+'</script>\n'+h[i:]
open(f'{W}/math-map.html','w',encoding='utf-8').write(h)
print(len(data), sum(len(r['papers']) for r in amc))
