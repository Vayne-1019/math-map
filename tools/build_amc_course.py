"""Merge data/amc_book.json (structure, answers) + data/amc_zh/chNN.json (our
Chinese text) + amc/figs.json -> amc/course.js (window.AMC_COURSE).

Course order follows the site's domains A, N, C, G. Chapters marked advanced
sit after a "difficulty rises" divider inside their domain.

data/amc_zh/chNN.txt (format in read_zh): our own chapter overview, and per
block label: title (theorem name), zh (statement, HTML + $LaTeX$), sol (our
rewritten solution), hint (ours), ans (override; else the book's answer).
Blocks of kind remark/note without a zh entry are dropped; untranslated
examples/problems are kept as "待翻譯" placeholders.
"""
import json, os, re, sys

ORDER = {"A": [13, 14, 15, 16, 17, 18, 19, 20, 21, 40, 41, 42, 43, 45],
         "N": [22, 23, 24, 25, 26, 27, 28, 29],
         "C": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
         "G": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 44]}
SECTION_ZH = {
    None: "觀念與例題", "Practice Problems": "練習題", "Additional Problems": "加練題",
    "Factorials": "階乘", "Permutations Basics": "排列的基本", "Permutations with Restrictions": "有限制的排列",
    "Word Rearrangements": "有相同物件的排列", "Combinations": "組合", "Subsets": "子集",
    "Probability Basics": "機率的基本", "Distinguishability": "可區分與不可區分",
    "Probability of Independent Events": "獨立事件的機率", "Probability of Dependent Events": "相依事件的機率",
    "Dependent or Independent Events?": "獨立還是相依？", "Casework": "分類討論", "Conditional Probability": "條件機率",
    "Complementary Counting with Symmetry": "補集與對稱", "Stars and Bars Fundamentals": "隔板法基本型",
    "Stars and Bars With Constraints": "有限制的隔板法", "Stars and Bars but Stars are groups": "把一組當成一顆星",
    "Stars and Bars to Count Orderings": "用隔板法數順序", "Basic Identities": "基本恆等式",
    "Vandermonde’s Identity": "范德蒙恆等式", "Pascal’s and Hockey Stick Identity": "巴斯卡恆等式與曲棍球棒恆等式",
    "Triangle Counting": "數三角形", "Rectangle Counting": "數長方形", "Square Counting": "數正方形",
    "Path Counting": "數路徑", "Polyhedrons": "多面體", "Geometric Probability in 3D": "立體的幾何機率",
    "Recursion Fundamentals": "遞迴基本型", "Recursion with Constraints": "有限制的遞迴",
    "More Complex Recursions": "較複雜的遞迴", "Multiple Recursions": "多條遞迴式",
    "States with Recursion": "狀態與遞迴", "Expected Value States": "期望值的狀態法",
    "Binomial Expansions": "二項式展開", "Quadratic Factorizations": "二次式的分解", "Cubic Factorizations": "三次式的分解",
    "Higher Power Factorizations": "高次式的分解", "Algebraic Equations": "代數方程", "Polynomials": "多項式",
    "Polynomial Root Representation": "用根表示多項式", "Symmetric Polynomials": "對稱多項式",
    "Polynomial Manipulations": "多項式的變形", "Telescoping": "裂項相消", "Work and Rate": "工作與效率",
    "Sum of Factors": "因數和", "Product of Factors": "因數積", "Simon’s Favorite Factoring Trick": "SFFT 配湊分解",
    "Sophie Germain’s Identity": "熱爾曼恆等式", "Palindromes": "回文數", "Chicken McNugget Theorem": "麥樂雞定理（兩數不能湊出的最大數）",
    "Basics of Angle Chasing": "角度追蹤基本", "Area of a Triangle": "三角形面積", "Triangle Properties": "三角形的性質",
    "Equilateral Triangle": "正三角形", "Right Triangles": "直角三角形", "Angle Bisector Theorem": "角平分線定理",
    "Square": "正方形", "Rectangle": "長方形", "Rhombus": "菱形", "Parallelogram": "平行四邊形", "Trapezoid": "梯形",
    "Circle Area": "圓面積", "Circle Length": "圓周與弧長", "Power of a Point": "圓冪", "Cyclic Quadrilaterals": "圓內接四邊形",
    "Hexagon": "正六邊形", "Octagon": "正八邊形", "Pentagons": "正五邊形", "Cube": "正方體", "Rectangular Prism": "長方體",
    "Cylinder": "圓柱", "Cone": "圓錐", "Sphere": "球", "Tetrahedron": "四面體", "Pyramid": "角錐",
    "Volume of Complex Polyhedrons": "複合立體的體積", "Cross Sections": "截面", "Area of Complex Shapes": "複合圖形的面積",
    "Length of complex shapes": "複合圖形的長度", "Line in Coordinate Plane": "坐標平面上的直線",
    "Circle in Coordinate Plane": "坐標平面上的圓", "Shoelace Theorem to find Area": "鞋帶公式求面積",
    "Picks Theorem (Optional)": "皮克定理（選讀）", "Trivial Inequality": "平方非負", "AM-GM": "算幾不等式",
    "Cauchy Schwarz": "柯西不等式", "Basic Definitions": "基本定義", "Logarithmic Formulas": "對數公式",
    "Trigonometric Identities": "三角恆等式", "More Trigonometric Identities": "更多三角恆等式",
    "Unit Circle Identities": "單位圓", "Pythagorean Identities": "平方關係", "Double Angle Identities": "倍角公式",
    "Addition and Subtraction Identities": "和角與差角公式", "Half Angle Identities": "半角公式",
    "Sum to Product Identities": "和差化積", "Product to Sum Identities": "積化和差",
    "Graphing to Solve Trigonometry Problems": "用圖形解三角題", "Periods and Graphs of Trigonometric Functions": "三角函數的週期與圖形",
    "Area of a Triangle using trigonometry": "用三角求三角形面積", "Law of Sines": "正弦定理", "Law of Cosines": "餘弦定理",
    "Basics": "基本", "Complex Numbers in Polynomials": "複數與多項式", "Complex Numbers in Trigonometry": "複數與三角",
}
KIND_ZH = {"definition": "定義", "theorem": "定理", "corollary": "推論", "lemma": "引理", "fact": "事實",
           "remark": "說明", "note": "附註", "example": "例題", "problem": "練習"}


def clean_answer(a):
    if not a:
        return None
    a = re.sub(r"\s+", " ", a).strip()
    a = re.sub(r"\^\{([^}]*)\}", r"^{\1}", a)
    return f"${a}$" if re.search(r"[\^_×√π]", a) else a


def src_label(s):
    if not s or s.lower().replace(" ", "") in ("omegalearn",):
        return "OmegaLearn 自編" if s else None
    return s


def read_zh(no):
    """data/amc_zh/chNN.txt — plain text so LaTeX needs no escaping:
        === intro
        <p>…</p>
        === § Factorials | 階乘          (section name)
        === 1.2.2 | 排列數
        zh: …            (fields: zh / sol / hint / ans; following lines continue the field)
    """
    f = f"data/amc_zh/ch{no:02d}.txt"
    if not os.path.exists(f):
        return {"items": {}}
    res, cur, field = {"items": {}}, None, None
    for line in open(f, encoding="utf-8").read().splitlines():
        m = re.match(r"^===\s*§\s*(.*?)\s*\|\s*(.*)$", line)
        if m:  # === § English section | 中文小節名
            res.setdefault("sections", {})[m.group(1)] = m.group(2).strip(); cur = field = None; continue
        m = re.match(r"^===\s*(\S+)\s*(?:\|\s*(.*))?$", line)
        if m:
            if m.group(1) == "intro":
                cur, field = res, "intro"; res["intro"] = ""
            else:
                cur = res["items"].setdefault(m.group(1), {}); field = None
                if m.group(2): cur["title"] = m.group(2).strip()
            continue
        m = re.match(r"^(zh|sol|hint|ans):\s?(.*)$", line)
        if m and cur is not None and cur is not res:
            field = m.group(1); cur[field] = m.group(2); continue
        if cur is not None and field:
            cur[field] = (cur.get(field) or "") + ("\n" if cur.get(field) else "") + line
    for it in list(res["items"].values()) + [res]:
        for k in ("zh", "sol", "hint", "ans", "intro"):
            if isinstance(it.get(k), str):
                it[k] = it[k].strip()
    return res


def main():
    book = json.load(open("data/amc_book.json", encoding="utf-8"))
    figs = json.load(open("amc/figs.json", encoding="utf-8"))
    chs = {c["no"]: c for c in book["chapters"]}
    out = []
    for dom, nos in ORDER.items():
        for no in nos:
            c = chs[no]
            zh = read_zh(no)
            Z = zh["items"]
            SEC = zh.get("sections", {})
            items = []
            for b in c["blocks"]:
                z = Z.get(b["label"], {})
                k = b["kind"]
                if k in ("remark", "note") and not z.get("zh"):
                    continue
                fk = b["label"] if k in ("example", "problem") else f"{k}:{b['label']}"
                it = {"kind": k, "label": b["label"], "section": SEC.get(b["section"]) or SECTION_ZH.get(b["section"], b["section"]), "page": b["page"],
                      "src": src_label(b["src"]) if k in ("example", "problem") else None,
                      "title": z.get("title"),
                      "zh": z.get("zh"), "sol": z.get("sol"), "hint": z.get("hint"),
                      "ans": z.get("ans") or clean_answer(b.get("answer")),
                      "figs": figs.get(fk, [])}
                if k not in ("example", "problem") and not it["zh"]:
                    continue  # untranslated theorem text is not shown
                items.append({kk: v for kk, v in it.items() if v not in (None, [], "")})
            probs = [i for i in items if i["kind"] in ("example", "problem")]
            out.append({"no": no, "zh": c["zh"], "en": c["en"], "domain": dom, "advanced": c["advanced"],
                        "units": c["units"], "pages": c["pages"], "intro": zh.get("intro"),
                        "done": sum(1 for i in probs if i.get("zh")), "total": len(probs), "items": items})
    os.makedirs("amc", exist_ok=True)
    js = "window.AMC_COURSE = " + json.dumps({"source": book["source"], "chapters": out}, ensure_ascii=False) + ";\n"
    open("amc/course.js", "w", encoding="utf-8").write(js)
    done = sum(c["done"] for c in out); total = sum(c["total"] for c in out)
    print(f"amc/course.js  {len(js)//1024} KB  translated {done}/{total} problems")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
