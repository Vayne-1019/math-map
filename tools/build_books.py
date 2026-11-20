"""Build the two book-derived layers of the site.

  data/books/<book>/book.txt        book info + planned lecture list (edited only by the main session)
  data/books/<book>/L<NN>.txt       one lecture, book order ("入口一：書本順序")
  data/units/<unit>/<book>-L<NN>.txt  digest of that lecture for one map unit ("入口二：單元地圖")

  -> books/<book>.js   window.BOOK_DATA[<book>]
  -> books/digest.js   window.UNIT_DIGEST[<unit>] = [ {from, title, order, html}, ... ]

File format: see docs/書本編譯規範.md. Blocks start with a line "=== <kind> [label] [| title]".
Raw-HTML blocks: text, body. Field blocks (定理 / 例 / 習題 / meta): "key: value" lines,
following lines continue the last key.
Markup: ⟦顯然｜拆解內容⟧  ->  "顯然 ▼" button that opens the breakdown in place (any short phrase
before ｜ works: 易知, 同理 …). Rendered with spans so it is valid inside <p>; the breakdown may use
inline HTML, <br>, $…$ and $$…$$, but no <p>/<div>/<ul>.
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
from geo import expand as geo_expand  # noqa: E402

RAW = {"text", "body"}
OB = re.compile(r"⟦([^｜⟦⟧]{1,12})｜(.*?)⟧", re.S)


FIG = re.compile(r'<figure class="bkfig">.*?</figure>', re.S)


def lift_figure(b):
    """Figures belong with the problem: readers re-check the picture while reading the solution.
    If the statement has no figure, move the first figure of the solution (or hint) up to it.
    At most one figure is added; later solution figures (step-by-step drawings) stay in place."""
    if FIG.search(b.get("zh", "") or ""):
        return b
    for k in ("sol", "hint"):
        m = FIG.search(b.get(k, "") or "")
        if m:
            rest = (b[k][:m.start()] + b[k][m.end():])
            b[k] = re.sub(r"<p>\s*</p>", "", rest).strip()
            b["zh"] = (b.get("zh", "") + "\n" + m.group(0)).strip()
            break
    return b


def markup(s):
    if not s:
        return s
    return OB.sub(lambda m: f'<span class="ob"><button type="button" class="obt" aria-expanded="false">{m.group(1)}</button><span class="obx" hidden>{m.group(2).strip()}</span></span>', s)


def parse(path):
    blocks, cur, key = [], None, None
    for line in open(path, encoding="utf-8").read().splitlines():
        m = re.match(r"^===\s*(\S+)\s*([^|]*?)\s*(?:\|\s*(.*))?$", line)
        if m:
            cur = {"kind": m.group(1), "label": m.group(2).strip(), "title": (m.group(3) or "").strip()}
            if cur["kind"] in RAW:
                cur["html"] = ""
            blocks.append(cur); key = None; continue
        if cur is None:
            continue
        if cur["kind"] in RAW:
            cur["html"] += line + "\n"; continue
        m = re.match(r"^([a-z]+):\s?(.*)$", line)
        if m:
            key = m.group(1); cur[key] = m.group(2); continue
        if key:
            cur[key] += "\n" + line
    for b in blocks:
        for k, v in list(b.items()):
            if isinstance(v, str):
                b[k] = v.strip()
    return blocks


def meta_of(blocks):
    m = next((b for b in blocks if b["kind"] == "meta"), {})
    return {k: v for k, v in m.items() if k not in ("kind", "label") and v != ""}


def book_info(book):
    info = meta_of(parse(f"data/books/{book}/book.txt"))
    parts, lectures = [], {}
    raw = open(f"data/books/{book}/book.txt", encoding="utf-8").read()
    sec = None
    for line in raw.splitlines():
        if line.startswith("==="):
            sec = line[3:].strip(); continue
        if not line.strip():
            continue
        if sec == "parts":
            name, rng = [x.strip() for x in line.split("|")]
            a, b = map(int, rng.split("-")); parts.append({"name": name, "from": a, "to": b})
        elif sec == "lectures":
            no, title, author, page = [x.strip() for x in line.split("|")]
            lectures[int(no)] = {"no": int(no), "title": title, "author": author, "page": int(page)}
    return info, parts, lectures


def build_book(book):
    info, parts, lectures = book_info(book)
    out = []
    for no, plan in sorted(lectures.items()):
        f = f"data/books/{book}/L{no:02d}.txt"
        if not os.path.exists(f):
            out.append({**plan, "status": "待編譯", "blocks": []}); continue
        blocks = parse(f)
        m = meta_of(blocks)
        items = []
        for b in blocks:
            if b["kind"] == "meta":
                continue
            if "zh" in b:
                b = lift_figure(b)
            it = {k: (markup(geo_expand(v)) if k in ("html", "zh", "sol", "hint", "ans") else v) for k, v in b.items()}
            items.append(it)
        out.append({"no": no, "title": m.get("title", plan["title"]), "author": m.get("author", plan["author"]),
                    "page": plan["page"], "pages": m.get("pages", ""), "status": m.get("status", "草稿"),
                    "units": [u.strip() for u in m.get("units", "").split(",") if u.strip()], "blocks": items})
    data = {"id": book, **info, "parts": parts, "lectures": out}
    js = f"window.BOOK_DATA = window.BOOK_DATA || {{}};\nwindow.BOOK_DATA[{json.dumps(book)}] = " + json.dumps(data, ensure_ascii=False) + ";\n"
    open(f"books/{book}.js", "w", encoding="utf-8").write(js)
    done = sum(1 for l in out if l["blocks"])
    print(f"books/{book}.js  {len(js)//1024} KB  {done}/{len(out)} lectures")


def build_digest():
    dig = {}
    for f in sorted(glob.glob("data/units/*/*.txt")):
        unit = os.path.basename(os.path.dirname(f))
        blocks = parse(f)
        m = meta_of(blocks)
        html = "\n".join(markup(geo_expand(b["html"])) for b in blocks if b["kind"] == "body")
        dig.setdefault(unit, []).append({"from": m.get("from", os.path.basename(f)[:-4]), "title": m.get("title", ""),
                                         "order": float(m.get("order", 50)), "html": html})
    for v in dig.values():
        v.sort(key=lambda d: (d["order"], d["from"]))
    js = "window.UNIT_DIGEST = " + json.dumps(dig, ensure_ascii=False) + ";\n"
    open("books/digest.js", "w", encoding="utf-8").write(js)
    print(f"books/digest.js  {len(js)//1024} KB  {sum(map(len, dig.values()))} digests in {len(dig)} units")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs("books", exist_ok=True)
    for b in ("cz", "gz"):
        build_book(b)
    build_digest()
