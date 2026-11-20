"""Parse the OmegaLearn AMC 10/12 book (data/AMC10.pdf) into data/amc_book.json.

Each chapter -> blocks (definition / theorem / remark / example / problem ...),
English text kept as extracted (superscripts as ^{..}, subscripts as _{..}).
Chapter -> site course order (A, N, C, G), ANCG unit links, and whether it sits
after the "difficulty rises" divider, are set in CHAPTERS below.
"""
import json, re, sys, pymupdf

PDF = "data/AMC10.pdf"
OUT = "data/amc_book.json"

# (book chapter no, zh title, course domain, advanced?, ANCG units)
CHAPTERS = {
    1: ("排列與組合", "C", False, ["C-1-1", "C-1-2", "C-1-6"]),
    2: ("機率", "C", False, ["C-3-1", "C-3-2"]),
    3: ("分類討論", "C", False, ["C-1-1"]),
    4: ("補集計數", "C", False, ["C-1-1", "C-1-5"]),
    5: ("排容原理", "C", False, ["C-1-5"]),
    6: ("隔板法（星與棒）", "C", False, ["C-1-3"]),
    7: ("組合恆等式", "C", False, ["C-1-4", "C-2-2"]),
    8: ("幾何計數", "C", False, ["C-1-2", "C-6-1"]),
    9: ("幾何機率", "C", False, ["C-3-1"]),
    10: ("期望值", "C", False, ["C-3-3"]),
    11: ("遞迴", "C", False, ["C-2-3"]),
    12: ("機率狀態", "C", False, ["C-3-4"]),
    13: ("代數變形", "A", False, ["A-1-2", "A-1-5"]),
    14: ("多項式的韋達定理", "A", False, ["A-2-3"]),
    15: ("多項式的根", "A", False, ["A-3-1", "A-3-2"]),
    16: ("等差數列", "A", False, ["A-7-1"]),
    17: ("等比數列", "A", False, ["A-7-1"]),
    18: ("特殊數列", "A", False, ["A-7-3", "A-7-4"]),
    19: ("平均數、中位數、眾數", "A", False, []),
    20: ("聯立方程", "A", False, ["A-2-5"]),
    21: ("速率、距離與時間", "A", False, ["A-2-5"]),
    22: ("質數與因數", "N", False, ["N-1-2", "N-4-1"]),
    23: ("整除與 Legendre 公式", "N", False, ["N-1-1", "N-5-2"]),
    24: ("最大公因數與最小公倍數", "N", False, ["N-1-3"]),
    25: ("同餘", "N", False, ["N-2-1", "N-2-2"]),
    26: ("代數式的數論", "N", False, ["N-1-1", "N-3-3"]),
    27: ("不定方程", "N", False, ["N-3-1", "N-3-3"]),
    28: ("進位制", "N", False, ["N-7-1"]),
    29: ("數論雜題", "N", False, ["N-7-2"]),
    30: ("角度追蹤", "G", False, ["G-1-1", "G-4-1"]),
    31: ("三角形的面積與長度", "G", False, ["G-1-4", "G-1-5"]),
    32: ("特殊三角形", "G", False, ["G-1-4"]),
    33: ("相似三角形", "G", False, ["G-1-3"]),
    34: ("四邊形", "G", False, ["G-1-2"]),
    35: ("圓", "G", False, ["G-4-1", "G-4-3", "G-4-4"]),
    36: ("多邊形", "G", False, ["G-1-1"]),
    37: ("立體幾何", "G", False, ["G-9-3", "G-9-4"]),
    38: ("複合圖形的面積與長度", "G", False, ["G-1-5"]),
    39: ("坐標幾何", "G", False, ["G-8-1", "G-8-2", "G-8-3"]),
    40: ("取整函數", "A", True, ["A-5-5", "N-4-3"]),
    41: ("不等式", "A", True, ["A-4-2", "A-4-3"]),
    42: ("對數", "A", True, ["A-1-4", "A-5-4"]),
    43: ("代數三角", "A", True, ["G-7-1", "G-7-3"]),
    44: ("幾何三角", "G", True, ["G-7-2", "G-7-5"]),
    45: ("複數", "A", True, ["A-8-1", "A-8-2", "A-8-3"]),
}

KINDS = "Definition|Theorem|Remark|Example|Problem|Note|Corollary|Fact|Lemma"
START = re.compile(rf"^({KINDS})\s+([\d.]+)\.?\s*(?:\((.*?)\))?\s*(.*)$")
SECTION = re.compile(r"^(\d+)\.(\d+)$")


def line_text(line):
    """Join spans, marking raised/lowered small spans as ^{} / _{}."""
    spans = [s for s in line["spans"] if s["text"]]
    if not spans:
        return ""
    base = max(s["size"] for s in spans)
    ys = [s["origin"][1] for s in spans if s["size"] >= base * 0.9]
    y0 = sorted(ys)[len(ys) // 2] if ys else spans[0]["origin"][1]
    out = ""
    for s in spans:
        t = s["text"]
        if s["size"] < base * 0.85 and t.strip():
            dy = s["origin"][1] - y0
            if dy < -1:
                t = "^{" + t.strip() + "}"
            elif dy > 1:
                t = "_{" + t.strip() + "}"
        out += t
    return out


def page_lines(page):
    d = page.get_text("dict")
    lines = []
    for b in d["blocks"]:
        for l in b.get("lines", []):
            t = line_text(l).rstrip()
            if t.strip():
                lines.append((t, l["bbox"][1], l["bbox"][3]))
    # drop running header / footer
    while lines and (lines[0][0].strip() == "OmegaLearn.org" or re.match(r"^Chapter \d+\. ", lines[0][0])):
        lines.pop(0)
    if lines and re.fullmatch(r"\d+", lines[-1][0].strip()):
        lines.pop()
    return lines


def main():
    doc = pymupdf.open(PDF)
    toc = [(t, p) for l, t, p in doc.get_toc() if l == 2]
    chapters = []
    for idx, (title, start) in enumerate(toc[:45]):
        no = idx + 1
        end = toc[idx + 1][1] - 1 if idx + 1 < len(toc) else doc.page_count
        zh, dom, adv, units = CHAPTERS[no]
        ch = {"no": no, "en": title, "zh": zh, "domain": dom, "advanced": adv, "units": units,
              "pages": [start, end], "blocks": []}
        section, cur, tail, tail_lines = None, None, None, {"Hints": [], "Answers": []}
        for pno in range(start - 1, end):
            page = doc[pno]
            plines = page_lines(page)
            lines = [t for t, _, _ in plines]
            if cur is not None and tail is None:
                cur["spans"].append([pno + 1, 0, None])
            i = 0
            while i < len(lines):
                s = lines[i].strip()
                y0 = plines[i][1]
                if s in ("Hints", "Answers"):
                    if cur is not None and tail is None and cur["spans"][-1][0] == pno + 1: cur["spans"][-1][2] = y0
                    tail = s; i += 1; continue
                if tail:
                    tail_lines[tail].append(s); i += 1; continue
                if s in ("Video Lecture", "Additional Problems") or re.fullmatch(r"Chapter \d+", s) or s == title:
                    i += 1; continue
                m = SECTION.match(s)
                if m and i + 1 < len(lines) and int(m.group(1)) == no:
                    if cur is not None: cur["spans"][-1][2] = y0
                    section = lines[i + 1].strip(); cur = None; i += 2; continue
                m = START.match(s)
                if m:
                    kind, label, src, rest = m.groups()
                    if cur is not None and cur["spans"][-1][0] == pno + 1: cur["spans"][-1][2] = y0
                    cur = {"spans": [[pno + 1, y0, None]], "kind": kind.lower(), "label": label.rstrip("."), "src": src, "section": section,
                           "page": pno + 1, "text": [rest] if rest else [], "solution": None,
                           "video": False}
                    ch["blocks"].append(cur); i += 1; continue
                if cur is None:
                    i += 1; continue
                if s == "Video Solution":
                    cur["video"] = True
                elif s == "Solution" and cur["solution"] is None:
                    cur["solution"] = []
                elif cur["solution"] is not None:
                    cur["solution"].append(lines[i])
                else:
                    cur["text"].append(lines[i])
                i += 1
        # hints / answers: lines starting with a block label begin a new entry
        labels = {b["label"] for b in ch["blocks"]}
        for key, out in (("Hints", "hint"), ("Answers", "answer")):
            cur_l, acc = None, {}
            for s in tail_lines[key]:
                m = re.match(r"^(\d+(?:\.\d+)+)\s*(.*)$", s)
                if m and m.group(1) in labels:
                    cur_l = m.group(1); acc[cur_l] = [m.group(2)]
                elif cur_l:
                    acc[cur_l].append(s)
            for b in ch["blocks"]:
                if b["label"] in acc:
                    b[out] = "\n".join(acc[b["label"]]).strip()
        for b in ch["blocks"]:
            b["text"] = "\n".join(b["text"]).strip()
            if b["solution"] is not None:
                b["solution"] = "\n".join(b["solution"]).strip()
        chapters.append(ch)
    json.dump({"source": "OmegaLearn, AMC 10/12 book (PDF, 2025-01)", "chapters": chapters},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for ch in chapters:
        k = {}
        for b in ch["blocks"]:
            k[b["kind"]] = k.get(b["kind"], 0) + 1
        print(ch["no"], ch["en"], ch["pages"], k)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
