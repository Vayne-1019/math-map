"""Clean Windows-OCR page texts: drop spaces between CJK chars, merge into one
markdown per book with page markers, and list lecture/chapter headings."""
import glob, os, re, sys
CJK = r"[　-〿㐀-鿿＀-￯]"
def clean(t):
    t = t.lstrip("﻿")
    for _ in range(2):
        t = re.sub(rf"({CJK}) +(?={CJK})", r"\1", t)
        t = re.sub(rf"({CJK}) +(?=[,.;:!?()（）])", r"\1", t)
        t = re.sub(rf"([,.;:!?()（）]) +(?={CJK})", r"\1", t)
    return t.replace(" ,", "，").replace(",", "，") if False else t
sys.stdout.reconfigure(encoding="utf-8")
for book in sys.argv[1:]:
    pages = sorted(glob.glob(os.path.join(book, "raw", "p*.txt")))
    out, heads = [], []
    for f in pages:
        n = int(os.path.basename(f)[1:5])
        t = clean(open(f, encoding="utf-8-sig").read()).strip()
        out.append(f"\n\n<!-- 第 {n} 頁（PDF 頁碼） -->\n\n{t}")
        for line in t.splitlines()[:4]:
            if re.match(r"^\s*第\s*\d+\s*[講讲章]", line):
                heads.append(f"p{n:03d}  {line.strip()}")
    open(os.path.join(book, "全文.md"), "w", encoding="utf-8").write(
        f"# {os.path.basename(book)}（OCR 全文）\n\n> Windows 內建 OCR 自動辨識。文字大致可讀，數學式多半失真，引用前請對照原書頁面。\n" + "".join(out))
    open(os.path.join(book, "目錄.txt"), "w", encoding="utf-8").write("\n".join(heads) + "\n")
    print(book, len(pages), "pages,", len(heads), "headings")
