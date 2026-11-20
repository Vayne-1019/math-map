"""Static checks for book lectures and unit digests.

usage: python -I tools/check_books.py [book ...]   (default: cz gz)
Checks: meta fields, status, unit codes exist in OUTLINE, digest `from` points to an
existing lecture, ⟦…｜…⟧ balanced and free of block tags, $ / $$ balanced, SVG
well-formed (viewBox, closed), no <img> of scans, simplified characters left in gz.
"""
import glob, os, re, sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(__file__))
from build_books import parse, meta_of  # noqa: E402
from geo import GEO, compile_geo, GeoError  # noqa: E402

OUTLINE = open("math-map.html", encoding="utf-8").read()
UNITS = set(re.findall(r"^([ANCG]-\d+-\d+) ", OUTLINE.split("const OUTLINE = `")[1].split("`;")[0], re.M))
SIMP = set("这们说为对时会从来个国过还发现问题与实际经进动没样关应处给头将该让总长电学书万东车门开间无运边体记许设识论变结证线约级组织绍类转边该观")

problems = []


def warn(f, msg):
    problems.append(f"{f}: {msg}")


def check_text(f, where, s, book):
    if not s:
        return
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", s):
        warn(f, f"{where}: 有控制字元（多半是 \\frac、\\beta 的反斜線被吃掉）")
    for gm in GEO.finditer(s):
        try:
            compile_geo(gm.group(1))
        except (GeoError, KeyError, ValueError, IndexError, ZeroDivisionError) as e:
            warn(f, f"{where}: 作圖腳本錯誤：{e}")
    if s.count("⟦") != s.count("⟧"):
        warn(f, f"{where}: ⟦ ⟧ 不成對")
    for m in re.finditer(r"⟦([^⟧]*)⟧", s, re.S):
        inner = m.group(1)
        if "｜" not in inner:
            warn(f, f"{where}: ⟦⟧ 少了 ｜")
        if re.search(r"<(p|div|ul|ol|table|figure)\b", inner):
            warn(f, f"{where}: ⟦⟧ 內含區塊標籤")
    t = re.sub(r"<svg.*?</svg>", "", s, flags=re.S)
    t = t.replace("\\$", "")
    dd = t.count("$$")
    if dd % 2:
        warn(f, f"{where}: $$ 不成對")
    if t.replace("$$", "").count("$") % 2:
        warn(f, f"{where}: $ 不成對")
    for m in re.finditer(r"<svg.*?</svg>", s, re.S):
        svg = m.group(0)
        if "viewBox" not in svg:
            warn(f, f"{where}: SVG 缺 viewBox")
        try:
            xml.dom.minidom.parseString(svg)
        except Exception as e:
            warn(f, f"{where}: SVG 格式錯誤 {str(e)[:60]}")
    if s.count("<svg") != s.count("</svg>"):
        warn(f, f"{where}: <svg> 未閉合")
    if re.search(r"<img\b", s):
        warn(f, f"{where}: 有 <img>（應自己畫 SVG）")
    if book == "gz":
        bad = sorted({c for c in re.sub(r"<[^>]+>|\$[^$]*\$", "", s) if c in SIMP})
        if bad:
            warn(f, f"{where}: 疑似簡體字 {''.join(bad)}")


def main(books):
    lectures = set()
    for book in books:
        for f in sorted(glob.glob(f"data/books/{book}/L*.txt")):
            no = int(re.search(r"L(\d+)", f).group(1)); lectures.add(f"{book}-L{no:02d}")
            bl = parse(f); m = meta_of(bl)
            if re.search(r"[²³₀-₉]", m.get("title", "")):
                warn(f, "標題用了 Unicode 上下標，請改成 $…$")
            for k in ("title", "pages", "units", "status"):
                if not m.get(k):
                    warn(f, f"meta 缺 {k}")
            if m.get("status") != "完成":
                warn(f, f"status = {m.get('status')}")
            for u in [x.strip() for x in m.get("units", "").split(",") if x.strip()]:
                if u not in UNITS:
                    warn(f, f"單元 {u} 不在大綱")
            for b in bl:
                if b.get("same"):
                    sm = re.match(r"(cz|gz)-L(\d+)\s+(\S+)\s*(\S+)$", b["same"])
                    tf = sm and f"data/books/{sm.group(1)}/L{int(sm.group(2)):02d}.txt"
                    if not sm or not os.path.exists(tf) or not any(x["kind"] == sm.group(3) and x.get("label") == sm.group(4) for x in parse(tf)):
                        warn(f, f"same: {b['same']} 找不到對應的題目")
                for k in ("html", "zh", "sol", "hint", "ans"):
                    check_text(f, f"{b['kind']} {b.get('label','')}/{k}", b.get(k), book)
    for f in sorted(glob.glob("data/units/*/*.txt")):
        unit = os.path.basename(os.path.dirname(f)); stem = os.path.basename(f)[:-4]
        if not any(stem.startswith(b + "-") for b in books):
            continue
        if unit not in UNITS:
            warn(f, f"單元資料夾 {unit} 不在大綱")
        bl = parse(f); m = meta_of(bl)
        if re.search(r"[²³₀-₉]", m.get("title", "")):
            warn(f, "標題用了 Unicode 上下標，請改成 $…$")
        if m.get("from") != stem:
            warn(f, f"from = {m.get('from')}，應為 {stem}")
        if stem not in lectures:
            warn(f, "對應的講次檔不存在")
        for b in bl:
            check_text(f, "body", b.get("html"), stem.split("-")[0])
    print(f"{len(lectures)} 講；{len(problems)} 個問題")
    for p in problems:
        print(" -", p)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:] or ["cz", "gz"])
