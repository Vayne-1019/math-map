import re, json, os, sys
src, out = sys.argv[1], sys.argv[2]
res=[]; rep=[]
for y in range(1989, 2027):
    t=open(os.path.join(src,f'apmo{y}_prb.txt'),encoding='utf-8').read()
    cand=list(re.finditer(r'(?m)^\s*(?:Question|Problem)\s*([1-5])\b\.?', t))
    ms=[]; want=1
    for m in cand:
        if int(m.group(1))==want: ms.append(m); want+=1
    if len(ms)<5:
        cand=list(re.finditer(r'(?m)^\s*\(?([1-5])[.)]\s', t)); ms=[]; want=1
        for m in cand:
            if int(m.group(1))==want: ms.append(m); want+=1
    for i,m in enumerate(ms):
        end=ms[i+1].start() if i+1<len(ms) else len(t)
        b=re.sub(r'-\n','',t[m.end():end].strip())
        res.append({'id':f'apmo{y}-{i+1}','contest':'APMO','year':y,'no':i+1,'statement_raw':b,
          'source':'https://apmo-official.org/problems',
          'pdf':f'https://apmo-official.org/static/problems/apmo{y}_prb.pdf',
          'solution_pdf':f'https://apmo-official.org/static/solutions/apmo{y}_sol.pdf','needs_check':True})
    rep.append((y,len(ms),min((len(t[m.end():(ms[i+1].start() if i+1<len(ms) else len(t))]) for i,m in enumerate(ms)),default=0)))
json.dump(res,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
for r in rep:
    if r[1]!=5 or r[2]<60: print(*r)
print('total',len(res))
