"""Render PDF pages to PNG for OCR. usage: render_pages.py <pdf> <outdir> [dpi] [first] [last]"""
import sys, os, pymupdf
pdf, out = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 200
d = pymupdf.open(pdf)
a = int(sys.argv[4]) if len(sys.argv) > 4 else 0
b = int(sys.argv[5]) if len(sys.argv) > 5 else d.page_count - 1
os.makedirs(out, exist_ok=True)
for i in range(a, b + 1):
    f = os.path.join(out, f"p{i+1:04d}.png")
    if not os.path.exists(f):
        d[i].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY).save(f)
print("rendered", a + 1, "to", b + 1)
