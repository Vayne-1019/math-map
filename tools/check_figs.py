"""比對作圖腳本產生的圖和原本手畫 SVG 的文字標示。

usage: python -I tools/check_figs.py <舊版 commit> [檔案 ...]
對每個由 <svg> 改成 <pre class="geo"> 的附圖（依同檔中的出現順序配對），
列出原圖有、新圖沒有的標示（少），以及新圖多出的大寫點名（多）。
下標 ₁ 與 tspan 下標都視為同一個字，例如 A₁ = A1。
"""
import re
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from geo import GEO, compile_geo  # noqa: E402

FIG = re.compile(r'<figure class="bkfig">.*?</figure>', re.S)
SUBS = str.maketrans("₀₁₂₃₄₅₆₇₈₉′", "0123456789'")


def texts(svg):
    out = set()
    for t in re.findall(r"<text[^>]*>(.*?)</text>", svg, re.S):
        t = re.sub(r"<[^>]+>", "", t)
        t = re.sub(r"\s+", "", t).translate(SUBS)
        if t:
            out.add(t)
    return out


def main(base, files):
    if not files:
        files = subprocess.run(["git", "diff", "--name-only", base, "HEAD", "--", "data/books", "data/units"],
                               capture_output=True, text=True, encoding="utf-8").stdout.split()
    tot = bad = 0
    for f in files:
        old = subprocess.run(["git", "show", f"{base}:{f}"], capture_output=True, text=True, encoding="utf-8").stdout
        new = open(f, encoding="utf-8").read()
        for i, (a, b) in enumerate(zip(FIG.findall(old), FIG.findall(new)), 1):
            g = GEO.search(b)
            if not g or GEO.search(a):
                continue
            tot += 1
            ta, tb = texts(a), texts(compile_geo(g.group(1))[0])
            less = sorted(ta - tb)
            more = sorted(x for x in tb - ta if re.fullmatch(r"[A-Z]\d*'*", x))
            if less or more:
                bad += 1
                print(f"{f} 第 {i} 張：" + (f"少 {' '.join(less)}" if less else "") + ("；" if less and more else "") + (f"多 {' '.join(more)}" if more else ""))
    print(f"作圖腳本 {tot} 張，標示不一致 {bad} 張")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2:])
