"""data/curriculum.txt -> curric.js

window.CURRIC[unit] = {k: 課|競, lv: 國|高|國高, d: C|B|A|S, codes, amc: [AMC 課程章號…]}
The AMC chapter list comes from CHAPTERS in tools/parse_amc_book.py (chapter -> units).
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from parse_amc_book import CHAPTERS  # noqa: E402

amc = {}
for no, (_zh, _dom, _adv, units) in sorted(CHAPTERS.items()):
    for u in units:
        amc.setdefault(u, []).append(no)

out = {}
for line in open("data/curriculum.txt", encoding="utf-8"):
    if not line.strip() or line.startswith("#"):
        continue
    u, k, lv, d, codes = [x.strip() for x in (line.rstrip("\n") + "|").split("|")[:5]]
    assert k in ("課", "競") and lv in ("國", "高", "國高") and d in "CBAS", line
    out[u] = {"k": k, "lv": lv, "d": d, "codes": codes}
    if u in amc:
        out[u]["amc"] = amc[u]
open("curric.js", "w", encoding="utf-8").write("window.CURRIC = " + json.dumps(out, ensure_ascii=False) + ";\n")
print(f"curric.js  {len(out)} units, {sum(1 for v in out.values() if 'amc' in v)} with AMC chapters")
