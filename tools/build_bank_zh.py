"""Chinese statements for the exam bank.

  data/bank_zh/<IMO|APMO>-<year>.txt   blocks "=== P<n>" with zh: / src: / note: fields
  -> bank/zh.js   window.BANK_ZH["IMO-1959"] = [ {zh, note}, ... ]  (index = problem number - 1)
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
from build_books import parse  # noqa: E402

out = {}
for f in sorted(glob.glob("data/bank_zh/*.txt")):
    key = os.path.basename(f)[:-4]
    rows = []
    for b in parse(f):
        m = re.match(r"P(\d+)$", b["kind"])
        if not m:
            continue
        n = int(m.group(1))
        while len(rows) < n:
            rows.append(None)
        rows[n - 1] = {k: b[k] for k in ("zh", "note") if b.get(k)}
    out[key] = rows
os.makedirs("bank", exist_ok=True)
js = "window.BANK_ZH = " + json.dumps(out, ensure_ascii=False) + ";\n"
open("bank/zh.js", "w", encoding="utf-8").write(js)
print(f"bank/zh.js  {len(js)//1024} KB  {len(out)} papers  {sum(1 for v in out.values() for r in v if r)} problems")
