import re, json, os, sys
src, out = sys.argv[1], sys.argv[2]
JUNK = re.compile(r'^(Language:.*|Day: ?\d.*|Time: .*|Each problem is worth.*|.*INTERNATIONAL MATHEMATICAL OLYMPIAD.*|.*International Mathematical Olympiad.*|First Day.*|Second Day.*|Time Limit.*|(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),.*)$', re.I)
res = []
for y in range(1959, 2027):
    p = os.path.join(src, f'{y}_eng.txt')
    if not os.path.exists(p): continue
    t = open(p, encoding='utf-8').read()
    lines = [l for l in t.split('\n') if not JUNK.match(l.strip())]
    t = '\n'.join(lines)
    pat = re.compile(rf'^(?:{y}/(\d)\.|Problem (\d)\.?(?=\s))', re.M)
    ms = list(pat.finditer(t))
    probs = []
    if not ms:
        # old style "1." numbering, two days restart
        cand = list(re.compile(r'^(\d)\. ', re.M).finditer(t)); ms=[]; want=1
        for m in cand:
            if int(m.group(1))==want: ms.append(m); want+=1
            elif want>3 and int(m.group(1))==want-3 and len(ms)==3: pass
        if len(ms)<6:  # numbering restarts on day 2
            ms=[]; want=1
            for m in cand:
                if int(m.group(1))==((want-1)%3)+1: ms.append(m); want+=1
    for i, m in enumerate(ms):
        end = ms[i+1].start() if i+1 < len(ms) else len(t)
        body = t[m.end():end].strip()
        probs.append(body)
    for i, b in enumerate(probs, 1):
        res.append({'id': f'imo{y}-{i}', 'contest': 'IMO', 'year': y, 'no': i,
                    'statement_raw': re.sub(r'-\n', '', b),
                    'source': f'https://www.imo-official.org/problems/{y}/',
                    'pdf': f'https://www.imo-official.org/assets/documents/problems/{y}/{y}_eng.pdf',
                    'needs_check': True})
    print(y, len(probs), min((len(b) for b in probs), default=0))
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
