"""data/curriculum.txt -> curric.js  (window.CURRIC[unit] = {k: 課|競, lv: 國|高|國高, d: C|B|A|S, codes})"""
import json, sys
out = {}
for line in open("data/curriculum.txt", encoding="utf-8"):
    if not line.strip() or line.startswith("#"):
        continue
    u, k, lv, d, codes = [x.strip() for x in (line.rstrip("\n") + "|").split("|")[:5]]
    assert k in ("課", "競") and lv in ("國", "高", "國高") and d in "CBAS", line
    out[u] = {"k": k, "lv": lv, "d": d, "codes": codes}
open("curric.js", "w", encoding="utf-8").write("window.CURRIC = " + json.dumps(out, ensure_ascii=False) + ";\n")
print(f"curric.js  {len(out)} units")
