import sys, os, pypdf
src, dst = sys.argv[1], sys.argv[2]
for f in sorted(os.listdir(src)):
    if not f.endswith('.pdf'): continue
    try:
        r = pypdf.PdfReader(os.path.join(src,f))
        t = '\n'.join((p.extract_text() or '') for p in r.pages)
        open(os.path.join(dst,f[:-4]+'.txt'),'w',encoding='utf-8').write(t)
        print(f, len(r.pages), len(t))
    except Exception as e:
        print(f, 'ERR', e)
