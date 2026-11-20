"""Crop only the figures (embedded images + vector drawings, not text) of each
block in data/amc_book.json -> amc/fig/<label>[_k].png, index in amc/figs.json."""
import json, os, sys, pymupdf
from PIL import Image

PDF, BOOK, OUTDIR = "data/AMC10.pdf", "data/amc_book.json", "amc/fig"
MIN = 36  # pt: ignore rules / bullets smaller than this


def clusters(rects):
    """Merge overlapping / nearby rects into figure boxes."""
    boxes = []
    for r in rects:
        r = pymupdf.Rect(r)
        for b in boxes:
            if (b + (-8, -8, 8, 8)).intersects(r):
                b.include_rect(r)
                break
        else:
            boxes.append(r)
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if (boxes[i] + (-8, -8, 8, 8)).intersects(boxes[j]):
                    boxes[i] |= boxes.pop(j); changed = True; break
            if changed: break
    return [b for b in boxes if b.width >= MIN and b.height >= MIN]


def main():
    doc = pymupdf.open(PDF)
    book = json.load(open(BOOK, encoding="utf-8"))
    os.makedirs(OUTDIR, exist_ok=True)
    index, cache = {}, {}
    for ch in book["chapters"]:
        for b in ch["blocks"]:
            out = []
            for pno, y0, y1 in b["spans"]:
                page = doc[pno - 1]
                if pno not in cache:
                    rs = [r for img in page.get_images(full=True) for r in page.get_image_rects(img[0])]
                    rs += [d["rect"] for d in page.get_drawings()
                           if d["rect"].width < page.rect.width * 0.6]  # skip example boxes / rules
                    boxes = clusters(rs)
                    # pull in point labels (A, B, 60°, ...) sitting just outside each drawing
                    allw = page.get_text("words")
                    per_line = {}
                    for w in allw:
                        per_line[(w[5], w[6])] = per_line.get((w[5], w[6]), 0) + 1
                    H = page.rect.height
                    words = [w for w in allw if len(w[4]) <= 4 and per_line[(w[5], w[6])] <= 3
                             and 85 < w[1] < H - 60]  # short labels only, never the running header/footer
                    for bx in boxes:
                        grow = bx + (-16, -16, 16, 16)
                        for w in words:
                            r = pymupdf.Rect(w[:4])
                            if grow.intersects(r):
                                bx.include_rect(r)
                    cache[pno] = boxes
                top, bot = y0 or 0, y1 if y1 is not None else page.rect.height
                for box in cache[pno]:
                    cy = (box.y0 + box.y1) / 2
                    if top - 2 <= cy <= bot + 2:
                        k = len(out)
                        name = f"{b['label']}{'_' + str(k + 1) if k else ''}.png"
                        pix = page.get_pixmap(dpi=150, clip=box + (-4, -4, 4, 4))
                        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        img.quantize(colors=32, method=Image.Quantize.MEDIANCUT).save(os.path.join(OUTDIR, name), optimize=True)
                        out.append(name)
            if out:
                index[b["label"] if b["kind"] in ("example", "problem") else b["kind"] + ":" + b["label"]] = out
    json.dump(index, open("amc/figs.json", "w", encoding="utf-8"), indent=0)
    print(len(index), "blocks with figures,", sum(map(len, index.values())), "images")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
