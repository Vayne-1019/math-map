"""幾何附圖的作圖腳本 → SVG ＋ 畫板資料。

書本檔案裡這樣寫（取代手畫的 <svg>）：

<figure class="bkfig"><pre class="geo">
A = (120, 30)
B = (40, 190)
C = (280, 190)
O = circumcenter(A, B, C)
k = circle(O, A)
H = foot(A, B, C)
D = second(k, A, O)
draw poly A B C
draw seg A H
draw seg A O D dash
draw seg D C dash
draw circle k
right B H A
</pre><figcaption>延長 AO 交圓於 D</figcaption></figure>

座標用 SVG 的像素（x 向右、y 向下），整張圖大約 320×220，寬不超過 360。
建置時算出所有點、畫出 SVG（線條用 currentColor），並把作圖步驟存進 data-geo，
網頁的畫板照同樣步驟重建：自由點可拖動，其餘的點、線、圓跟著動，關係（垂足、外心、交點…）都保留。

點
  A = (x, y)                自由點（可拖動）
  P = on(k, x, y)           在圓 k 或直線 l 上、可沿著滑動的點
  M = mid(A, B)             中點
  P = along(A, B, t)        A + t(B − A)，t 是數字（例如 1/3 → 0.3333）
  O = circumcenter(A, B, C) 外心；incenter 內心；centroid 重心；orthocenter 垂心
  H = foot(P, A, B)         P 到直線 AB 的垂足
  X = inter(A, B, C, D)     直線 AB 與直線 CD 的交點
  X = second(k, A, B)       直線 AB 與圓 k 除了 A 以外的另一個交點（A 要在圓上）
  X = meet(a, b, x, y)      兩個物件（直線或圓）的交點中，靠近 (x, y) 的那一個
  P2 = reflect(P, A, B)     P 對直線 AB 的鏡射；rotate(P, O, 度數)；scale(P, O, 倍數)；
  P2 = reflectp(P, O)       P 對點 O 的對稱點
  T = tangent(P, k, x, y)   從圓外點 P 到圓 k 的切點中，靠近 (x, y) 的那一個
物件（不會自動畫出來）
  l = line(A, B)            直線
  k = circle(O, A)          圓心 O、過 A；circle3(A, B, C) 過三點；circler(O, 半徑像素)
畫
  draw seg A B C …          折線（連續的線段）；draw poly A B C … 封閉多邊形（加 fill 會淡淡上色）
  draw line A B             直線；draw ray A B 射線（從 A 出發）
  draw circle k             畫圓
  選項接在後面：dash（虛線）、accent（橘色強調）
  right A H B               在 H 畫直角記號（∠AHB 是直角）
  angle A B C               在 B 畫角的弧線記號（加 accent 會上色）
  label A ne                名稱擺放方向 n ne e se s sw w nw（不寫就自動擺在離圖中心遠的一側）
  hide A                    只當輔助點，不畫點也不標名稱
  dot A                     點只畫圓點不標名稱
"""
import html, json, math, re

DIRS = {"n": (0, -1), "ne": (0.75, -0.75), "e": (1, 0), "se": (0.75, 0.75), "s": (0, 1), "sw": (-0.75, 0.75), "w": (-1, 0), "nw": (-0.75, -0.75)}
WARM = "#c2562b"


class GeoError(Exception):
    pass


def _num(s):
    s = s.strip()
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def mul(a, t): return (a[0] * t, a[1] * t)
def dot(a, b): return a[0] * b[0] + a[1] * b[1]
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])


def circumcenter(a, b, c):
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-12:
        raise GeoError("三點共線，沒有外心")
    ux = ((a[0] ** 2 + a[1] ** 2) * (b[1] - c[1]) + (b[0] ** 2 + b[1] ** 2) * (c[1] - a[1]) + (c[0] ** 2 + c[1] ** 2) * (a[1] - b[1])) / d
    uy = ((a[0] ** 2 + a[1] ** 2) * (c[0] - b[0]) + (b[0] ** 2 + b[1] ** 2) * (a[0] - c[0]) + (c[0] ** 2 + c[1] ** 2) * (b[0] - a[0])) / d
    return (ux, uy)


def foot(p, a, b):
    d = sub(b, a); t = dot(sub(p, a), d) / (dot(d, d) or 1e-12)
    return add(a, mul(d, t))


def line_line(a, b, c, d):
    r, s = sub(b, a), sub(d, c); den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        raise GeoError("兩直線平行，沒有交點")
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    return add(a, mul(r, t))


def line_circle(a, b, o, r):
    d = sub(b, a); f = sub(a, o)
    A = dot(d, d); B = 2 * dot(f, d); C = dot(f, f) - r * r; disc = B * B - 4 * A * C
    if disc < -1e-9:
        raise GeoError("直線和圓不相交")
    disc = max(disc, 0) ** 0.5
    return [add(a, mul(d, (-B - disc) / (2 * A))), add(a, mul(d, (-B + disc) / (2 * A)))]


def circle_circle(o1, r1, o2, r2):
    d = dist(o1, o2)
    if d < 1e-12 or d > r1 + r2 + 1e-9 or d < abs(r1 - r2) - 1e-9:
        raise GeoError("兩圓不相交")
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d); h = max(r1 * r1 - a * a, 0) ** 0.5
    m = add(o1, mul(sub(o2, o1), a / d)); u = mul(sub(o2, o1), 1 / d)
    return [(m[0] - u[1] * h, m[1] + u[0] * h), (m[0] + u[1] * h, m[1] - u[0] * h)]


def parse(text):
    """→ list of ops (dicts) in order."""
    ops = []
    for raw in text.strip().splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        m = re.match(r"^(\S+)\s*=\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)$", line)
        if m:
            ops.append({"op": "free", "name": m.group(1), "args": [], "xy": [float(m.group(2)), float(m.group(3))]}); continue
        m = re.match(r"^(\S+)\s*=\s*([a-z0-9]+)\((.*)\)$", line)
        if m:
            args = [a.strip() for a in m.group(3).split(",")]
            ops.append({"op": m.group(2), "name": m.group(1), "args": args}); continue
        w = line.split()
        if w[0] in ("draw", "right", "angle", "label", "hide", "dot", "size"):
            ops.append({"op": w[0], "args": w[1:]}); continue
        raise GeoError(f"看不懂這一行：{raw}")
    return ops


def evaluate(ops):
    """Compute coordinates. Returns (P, OBJ) with P[name]=(x,y), OBJ[name]=('line',A,B)|('circle',center,r)."""
    P, OBJ = {}, {}

    def pt(n):
        if n not in P:
            raise GeoError(f"還沒定義點 {n}")
        return P[n]

    def obj(n):
        if n in OBJ:
            return OBJ[n]
        raise GeoError(f"還沒定義物件 {n}")

    def hits(o1, o2):
        a, b = OBJ_geom(o1), OBJ_geom(o2)
        if a[0] == "line" and b[0] == "line":
            return [line_line(a[1], a[2], b[1], b[2])]
        if a[0] == "line":
            return line_circle(a[1], a[2], b[1], b[2])
        if b[0] == "line":
            return line_circle(b[1], b[2], a[1], a[2])
        return circle_circle(a[1], a[2], b[1], b[2])

    def OBJ_geom(n):
        o = obj(n)
        if o[0] == "line":
            return ("line", pt(o[1]), pt(o[2]))
        return o

    for op in ops:
        k, n, a = op["op"], op.get("name"), op.get("args", [])
        if k in ("draw", "right", "angle", "label", "hide", "dot", "size"):
            continue
        if k == "free":
            P[n] = tuple(op["xy"])
        elif k == "on":
            o = OBJ_geom(a[0]); q = (_num(a[1]), _num(a[2]))
            if o[0] == "line":
                P[n] = foot(q, o[1], o[2])
            else:
                v = sub(q, o[1]); L = math.hypot(*v) or 1; P[n] = add(o[1], mul(v, o[2] / L))
            op["xy"] = list(P[n])
        elif k == "mid":
            P[n] = mul(add(pt(a[0]), pt(a[1])), 0.5)
        elif k == "along":
            A, B = pt(a[0]), pt(a[1]); P[n] = add(A, mul(sub(B, A), _num(a[2])))
        elif k == "circumcenter":
            P[n] = circumcenter(pt(a[0]), pt(a[1]), pt(a[2]))
        elif k == "centroid":
            A, B, C = (pt(x) for x in a); P[n] = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
        elif k == "incenter":
            A, B, C = (pt(x) for x in a); la, lb, lc = dist(B, C), dist(C, A), dist(A, B); s = la + lb + lc
            P[n] = ((la * A[0] + lb * B[0] + lc * C[0]) / s, (la * A[1] + lb * B[1] + lc * C[1]) / s)
        elif k == "orthocenter":
            A, B, C = (pt(x) for x in a); O = circumcenter(A, B, C); P[n] = (A[0] + B[0] + C[0] - 2 * O[0], A[1] + B[1] + C[1] - 2 * O[1])
        elif k == "foot":
            P[n] = foot(pt(a[0]), pt(a[1]), pt(a[2]))
        elif k == "inter":
            P[n] = line_line(*(pt(x) for x in a[:4]))
        elif k == "second":
            c = OBJ_geom(a[0]); A, B = pt(a[1]), pt(a[2]); two = line_circle(A, B, c[1], c[2])
            P[n] = max(two, key=lambda q: dist(q, A))
        elif k == "meet":
            q = (_num(a[2]), _num(a[3])); P[n] = min(hits(a[0], a[1]), key=lambda z: dist(z, q))
        elif k == "tangent":
            Pp, c = pt(a[0]), OBJ_geom(a[1]); q = (_num(a[2]), _num(a[3]))
            m = mul(add(Pp, c[1]), 0.5); P[n] = min(circle_circle(c[1], c[2], m, dist(Pp, c[1]) / 2), key=lambda z: dist(z, q))
        elif k == "reflect":
            p, f = pt(a[0]), foot(pt(a[0]), pt(a[1]), pt(a[2])); P[n] = (2 * f[0] - p[0], 2 * f[1] - p[1])
        elif k == "reflectp":
            p, o = pt(a[0]), pt(a[1]); P[n] = (2 * o[0] - p[0], 2 * o[1] - p[1])
        elif k == "rotate":
            # 角度以數學方向（逆時針）為正；SVG 的 y 向下，所以這裡取負
            p, o, t = pt(a[0]), pt(a[1]), -math.radians(_num(a[2])); v = sub(p, o)
            P[n] = (o[0] + v[0] * math.cos(t) - v[1] * math.sin(t), o[1] + v[0] * math.sin(t) + v[1] * math.cos(t))
        elif k == "scale":
            p, o = pt(a[0]), pt(a[1]); P[n] = add(o, mul(sub(p, o), _num(a[2])))
        elif k == "line":
            pt(a[0]); pt(a[1]); OBJ[n] = ("line", a[0], a[1])
        elif k == "circle":
            OBJ[n] = ("circle", pt(a[0]), dist(pt(a[0]), pt(a[1])))
        elif k == "circle3":
            O = circumcenter(*(pt(x) for x in a)); OBJ[n] = ("circle", O, dist(O, pt(a[0])))
        elif k == "circler":
            OBJ[n] = ("circle", pt(a[0]), _num(a[1]))
        else:
            raise GeoError(f"不認得的指令 {k}")
    return P, OBJ


def render(ops, P, OBJ):
    hidden = {a for op in ops if op["op"] == "hide" for a in op["args"]}
    dots = {a for op in ops if op["op"] == "dot" for a in op["args"]}
    ldir = {op["args"][0]: op["args"][1] for op in ops if op["op"] == "label" and len(op["args"]) >= 2}
    shapes, marks, used = [], [], set()
    xs, ys = [], []

    def ext(p, r=0):
        xs.extend([p[0] - r, p[0] + r]); ys.extend([p[1] - r, p[1] + r])

    def style(opts):
        s = ' stroke-dasharray="5 4" stroke-width="1.3"' if "dash" in opts else ""
        if "accent" in opts:
            s += f' stroke="{WARM}"'
        return s

    for op in ops:
        if op["op"] != "draw":
            continue
        kind, rest = op["args"][0], op["args"][1:]
        opts = {w for w in rest if w in ("dash", "accent", "fill")}
        names = [w for w in rest if w not in opts]
        if kind in ("seg", "poly"):
            pts = [P[x] for x in names]; used.update(names); [ext(p) for p in pts]
            ptxt = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)
            if kind == "poly":
                fill = f' fill="currentColor" fill-opacity="0.07"' if "fill" in opts else ""
                shapes.append(f'<polygon points="{ptxt}"{fill}{style(opts)}/>')
            else:
                shapes.append(f'<polyline points="{ptxt}"{style(opts)}/>')
        elif kind in ("line", "ray"):
            A, B = P[names[0]], P[names[1]]; used.update(names[:2]); d = sub(B, A); L = math.hypot(*d) or 1; u = mul(d, 1 / L)
            s0 = A if kind == "ray" else add(A, mul(u, -60)); s1 = add(B, mul(u, 60))
            ext(A); ext(B)
            shapes.append(f'<line x1="{s0[0]:.1f}" y1="{s0[1]:.1f}" x2="{s1[0]:.1f}" y2="{s1[1]:.1f}"{style(opts)}/>')
            op["_ends"] = [s0, s1]
        elif kind == "circle":
            o = OBJ[names[0]]; ext(o[1], o[2])
            shapes.append(f'<circle cx="{o[1][0]:.1f}" cy="{o[1][1]:.1f}" r="{o[2]:.1f}"{style(opts)}/>')
    for op in ops:
        if op["op"] == "right":
            A, H, B = (P[x] for x in op["args"][:3]); u = sub(A, H); v = sub(B, H)
            u = mul(u, 7 / (math.hypot(*u) or 1)); v = mul(v, 7 / (math.hypot(*v) or 1))
            p1, p2, p3 = add(H, u), add(add(H, u), v), add(H, v)
            marks.append(f'<polyline points="{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}" stroke-width="1"/>')
        elif op["op"] == "angle":
            A, Bv, C = (P[x] for x in op["args"][:3]); r = 14
            a1 = math.atan2(A[1] - Bv[1], A[0] - Bv[0]); a2 = math.atan2(C[1] - Bv[1], C[0] - Bv[0])
            da = (a2 - a1) % (2 * math.pi)
            if da > math.pi:
                a1, a2, da = a2, a1, 2 * math.pi - da
            s = (Bv[0] + r * math.cos(a1), Bv[1] + r * math.sin(a1)); e = (Bv[0] + r * math.cos(a1 + da), Bv[1] + r * math.sin(a1 + da))
            col = f' stroke="{WARM}"' if "accent" in op["args"] else ""
            marks.append(f'<path d="M{s[0]:.1f},{s[1]:.1f} A{r},{r} 0 0 1 {e[0]:.1f},{e[1]:.1f}" stroke-width="1.2"{col}/>')
    # 標名稱：大寫開頭的點
    named = [n for n in P if re.match(r"^[A-Z]", n) and n not in hidden]
    for n in named:
        ext(P[n])
    cx = sum(P[n][0] for n in named) / max(len(named), 1); cy = sum(P[n][1] for n in named) / max(len(named), 1)
    labels, dotsvg = [], []
    for n in named:
        p = P[n]
        if n in ldir:
            d = DIRS[ldir[n]]
        else:
            v = sub(p, (cx, cy)); L = math.hypot(*v)
            d = (0, -1) if L < 1 else mul(v, 1 / L)
        lx, ly = p[0] + d[0] * 13, p[1] + d[1] * 13 + 5
        base = n.rstrip("'′")
        prime = "′" * (len(n) - len(base))
        sub_m = re.match(r"^([A-Z])(\d+)$", base)
        txt = f'{sub_m.group(1)}<tspan font-size="10" dy="3">{sub_m.group(2)}</tspan>' if sub_m else html.escape(base)
        labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle">{txt}{prime}</text>')
        ext((lx, ly - 5), 9)
        dotsvg.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="2.2"/>')
    for n in dots:
        if n in P and n not in named:
            dotsvg.append(f'<circle cx="{P[n][0]:.1f}" cy="{P[n][1]:.1f}" r="2.2"/>')
    if not xs:
        raise GeoError("沒有畫任何東西")
    pad = 6
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    w, h = x1 - x0, y1 - y0
    disp = min(360, round(w))
    svg = (f'<svg viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}" width="{disp}" role="img">'
           f'<g fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round">{"".join(shapes)}{"".join(marks)}</g>'
           f'<g fill="currentColor">{"".join(dotsvg)}</g>'
           f'<g fill="currentColor" font-size="15" font-style="italic" font-family="Times New Roman, serif">{"".join(labels)}</g></svg>')
    return svg, [round(x0), round(y0), round(w), round(h)]


def compile_geo(text):
    ops = parse(text)
    P, OBJ = evaluate(ops)
    svg, vb = render(ops, P, OBJ)
    data = {"vb": vb, "ops": [{k: v for k, v in op.items() if not k.startswith("_")} for op in ops]}
    return svg, data


GEO = re.compile(r'<pre class="geo">(.*?)</pre>', re.S)


def expand(htmltext):
    """Replace every <pre class="geo"> with the rendered SVG and put the steps on the <figure>."""
    if not htmltext or '<pre class="geo">' not in htmltext:
        return htmltext
    out, pos = [], 0
    for m in GEO.finditer(htmltext):
        svg, data = compile_geo(html.unescape(m.group(1)))
        before = htmltext[pos:m.start()]
        fi = before.rfind('<figure class="bkfig"')
        if fi >= 0 and 'data-geo' not in before[fi:]:
            attr = html.escape(json.dumps(data, ensure_ascii=False, separators=(",", ":")), quote=True)
            before = before[:fi] + f'<figure class="bkfig" data-geo="{attr}"' + before[fi + len('<figure class="bkfig"'):]
        out.append(before); out.append(svg); pos = m.end()
    out.append(htmltext[pos:])
    return "".join(out)
