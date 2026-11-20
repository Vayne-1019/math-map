/* 畫板：工具分組仿動態幾何軟體的做法（點／線／作圖／圓／變換／量測／顯示），
   支援滾輪與雙指縮放、拖曳空白處平移；可以把書上的 SVG 附圖匯入成可拖動的圖。
   GeoBoard.mount(container, { svg })  → 回傳 { board, destroy } */
(function () {
  'use strict';
  const CSSV = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const pal = () => ({ fg: CSSV('--fg') || '#172033', muted: CSSV('--muted') || '#5a6478', accent: CSSV('--accent') || '#2a55b8', warm: '#c2562b', line: CSSV('--line') || '#d9dee7' });

  const GROUPS = [
    { g: '移動', tools: [['move', '移動', '拖動點；拖空白處可移動畫面，滾輪或雙指縮放。']] },
    { g: '點', tools: [['point', '點', '點一下放一個點；點在線或圓上會黏在上面。'], ['intersect', '交點', '點兩個物件（線、圓）。'], ['midpoint', '中點', '點兩個點。']] },
    { g: '線', tools: [['segment', '線段', '點兩個點。'], ['line', '直線', '點兩個點。'], ['ray', '射線', '先點起點，再點方向上的一點。'], ['polygon', '多邊形', '依序點頂點，最後再點一次第一個頂點。']] },
    { g: '作圖', tools: [['perp', '垂線', '先點一個點，再點一條線。'], ['parallel', '平行線', '先點一個點，再點一條線。'], ['pbis', '中垂線', '點兩個點。'], ['abis', '角平分線', '依序點三個點，中間那個是頂點。'], ['tangent', '切線', '先點圓外一點，再點圓。']] },
    { g: '圓', tools: [['circle', '圓：圓心與圓上一點', '先點圓心，再點圓上一點。'], ['circle3', '圓：過三點', '點三個點。'], ['circler', '圓：圓心與半徑', '點圓心，再輸入半徑。']] },
    { g: '變換', tools: [['reflectL', '對直線鏡射', '先點要鏡射的物件，再點對稱軸。'], ['reflectP', '點對稱', '先點要對稱的物件，再點對稱中心。'], ['rotate', '旋轉', '先點要旋轉的物件，再點旋轉中心，然後輸入角度。'], ['dilate', '位似', '先點物件，再點位似中心，然後輸入倍數。'], ['invert', '反演', '先點要反演的物件，再點反演圓。']] },
    { g: '量測', tools: [['dist', '距離', '點兩個點。'], ['angle', '角度', '依序點三個點，中間那個是頂點。']] },
    { g: '顯示', tools: [['hide', '隱藏', '點物件把它藏起來；「物件」清單裡可以再打開。'], ['label', '名稱', '點物件切換顯示名稱。']] },
  ];
  const TOOL = {}; GROUPS.forEach(g => g.tools.forEach(([k, n, h]) => { TOOL[k] = { name: n, hint: h, group: g.g }; }));

  let uid = 0;
  function mount(host, opt) {
    opt = opt || {};
    const c = pal();
    host.classList.add('gb');
    host.innerHTML = `
      <div class="gb-groups" role="tablist">${GROUPS.map((g, i) => `<button type="button" role="tab" data-g="${i}"${i === 0 ? ' class="on"' : ''}>${g.g}</button>`).join('')}</div>
      <div class="gb-tools"></div>
      <div class="gb-status" aria-live="polite"></div>
      <div class="gb-stage"><div class="gb-box"></div>
        <div class="gb-view"><button type="button" data-v="in" title="放大">＋</button><button type="button" data-v="out" title="縮小">－</button><button type="button" data-v="fit" title="回到原本的範圍">⤢</button></div></div>
      <div class="gb-foot"><button type="button" data-a="undo">復原</button><button type="button" data-a="clear">清除</button><button type="button" data-a="list" aria-expanded="false">物件</button></div>
      <div class="gb-list" hidden></div>`;
    const $ = s => host.querySelector(s);
    const box = $('.gb-box'); box.id = 'gbx' + (++uid);
    const spec = opt.svg ? parseSVG(opt.svg) : null;
    const bbox0 = spec ? spec.bbox : [-6, 4.5, 6, -4.5];
    const b = JXG.JSXGraph.initBoard(box.id, {
      boundingbox: bbox0, keepaspectratio: true, axis: false, showCopyright: false, showNavigation: false,
      pan: { enabled: true, needShift: false, needTwoFingers: false },
      zoom: { enabled: true, wheel: true, needShift: false, pinch: true, min: 0.05, max: 40, factorX: 1.15, factorY: 1.15 },
    });
    const fit = () => b.setBoundingBox(bbox0, true);
    let ro = null;
    let lastW = 0, lastH = 0;
    const resize = () => { const w = box.clientWidth, h = box.clientHeight; if (w < 20 || h < 20 || (Math.abs(w - lastW) < 2 && Math.abs(h - lastH) < 2)) return; lastW = w; lastH = h; try { b.resizeContainer(w, h, true, true); fit(); } catch (_) {} };
    if (window.ResizeObserver) { ro = new ResizeObserver(resize); ro.observe(box); }
    requestAnimationFrame(resize);

    let mode = 'move', picks = [], hist = [], letter = 0;
    const used = new Set();
    const nextName = () => { const s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'; for (;;) { const n = s[letter % 26] + (letter >= 26 ? Math.floor(letter / 26) : ''); letter++; if (!used.has(n)) { used.add(n); return n; } } };
    const PT = (name, col) => ({ name, size: 3.5, strokeColor: col || c.fg, fillColor: col || c.fg, label: { strokeColor: col || c.fg, fontSize: 15, cssStyle: 'font-style:italic;font-family:"Times New Roman",serif' } });
    const newPoint = (xy, on, name) => { const n = name || nextName(); used.add(n); return on ? b.create('glider', [xy[0], xy[1], on], PT(n)) : b.create('point', xy, PT(n)); };
    const LINE = { strokeColor: c.fg, strokeWidth: 2, highlightStrokeColor: c.accent };
    const DERIVED = { strokeColor: c.accent, strokeWidth: 1.6, highlightStrokeColor: c.accent };
    const helper = (fx, fy) => { const o = b.create('point', [fx, fy], { visible: false, withLabel: false, name: '' }); o.gbHelper = true; return o; };

    const status = $('.gb-status');
    const setStatus = (extra) => { const t = TOOL[mode]; status.textContent = (extra || t.hint) + (picks.length ? `（已選 ${picks.length} 個）` : ''); };
    const showTools = gi => {
      host.querySelectorAll('.gb-groups button').forEach(x => x.classList.toggle('on', +x.dataset.g === gi));
      $('.gb-tools').innerHTML = GROUPS[gi].tools.map(([k, n]) => `<button type="button" data-m="${k}"${k === mode ? ' class="on"' : ''}>${n}</button>`).join('');
    };
    const setMode = m => { mode = m; picks = []; host.querySelectorAll('.gb-tools button').forEach(x => x.classList.toggle('on', x.dataset.m === m)); setStatus(); };

    const isPt = o => o.elementClass === JXG.OBJECT_CLASS_POINT;
    const isLine = o => o.elementClass === JXG.OBJECT_CLASS_LINE;
    const isCirc = o => o.elementClass === JXG.OBJECT_CLASS_CIRCLE;
    const isCurve = o => o.elementClass === JXG.OBJECT_CLASS_CURVE && o.type !== JXG.OBJECT_TYPE_ANGLE;
    const visible = o => o.visPropCalc && o.visPropCalc.visible;
    const hit = (pos, test) => { const os = Object.values(b.objects).filter(o => test(o) && visible(o) && o.hasPoint && o.hasPoint(pos[0], pos[1])); return os.find(isPt) || os[0]; };
    const commit = els => { hist.push(els.filter(Boolean)); picks = []; setStatus(); refreshList(); };
    const ask = (q, d) => { const v = window.prompt(q, d); if (v === null) return null; const x = parseFloat(String(v).replace('°', '')); return isFinite(x) ? x : null; };

    /* 變換：把點映到點；線、圓、多邊形用它們的定義點去映 */
    const mapPoint = (p, f, col) => { const q = () => f(p.X(), p.Y()); const o = b.create('point', [() => q()[0], () => q()[1]], PT(nextName() , col || c.warm)); o.setAttribute({ name: (p.name || '') ? p.name + '′' : o.name }); return o; };
    const definingPoints = o => {
      if (isPt(o)) return [o];
      if (isLine(o)) return [o.point1, o.point2];
      if (isCirc(o)) { const p2 = helper(() => o.center.X() + o.Radius(), () => o.center.Y()); return [o.center, p2]; }
      if (o.type === JXG.OBJECT_TYPE_POLYGON) return o.vertices.slice(0, -1);
      return null;
    };
    const transform = (o, f) => {
      const src = definingPoints(o); if (!src) return [];
      const imgs = src.map(p => mapPoint(p, f));
      if (isPt(o)) return imgs;
      if (isLine(o)) { const st = o.visProp; return imgs.concat(b.create('line', imgs, { strokeColor: c.warm, strokeWidth: 2, straightFirst: st.straightfirst, straightLast: st.straightlast })); }
      if (isCirc(o)) { imgs[1].setAttribute({ visible: false }); return imgs.concat(b.create('circle', imgs, { strokeColor: c.warm, strokeWidth: 2 })); }
      return imgs.concat(b.create('polygon', imgs, { fillColor: c.warm, fillOpacity: 0.12, borders: { strokeColor: c.warm, strokeWidth: 2 } }));
    };
    const reflectLineF = l => (x, y) => { const x1 = l.point1.X(), y1 = l.point1.Y(), dx = l.point2.X() - x1, dy = l.point2.Y() - y1, t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy || 1); const fx = x1 + t * dx, fy = y1 + t * dy; return [2 * fx - x, 2 * fy - y]; };
    const reflectPtF = cp => (x, y) => [2 * cp.X() - x, 2 * cp.Y() - y];
    const rotateF = (cp, deg) => { const a = deg * Math.PI / 180, cs = Math.cos(a), sn = Math.sin(a); return (x, y) => { const dx = x - cp.X(), dy = y - cp.Y(); return [cp.X() + cs * dx - sn * dy, cp.Y() + sn * dx + cs * dy]; }; };
    const dilateF = (cp, k) => (x, y) => [cp.X() + k * (x - cp.X()), cp.Y() + k * (y - cp.Y())];
    const invF = circ => (x, y) => { const ox = circ.center.X(), oy = circ.center.Y(), r2 = circ.Radius() ** 2, dx = x - ox, dy = y - oy, d2 = dx * dx + dy * dy || 1e-12; return [ox + r2 * dx / d2, oy + r2 * dy / d2]; };
    /* 反演：點直接算；線、圓、線段用參數曲線，經過反演中心時自動變成直線或圓 */
    const invert = (o, circ) => {
      const f = invF(circ);
      if (isPt(o)) return [mapPoint(o, f)];
      let X, Y, a, z;
      if (isCirc(o)) { X = t => o.center.X() + o.Radius() * Math.cos(t); Y = t => o.center.Y() + o.Radius() * Math.sin(t); a = 0; z = 2 * Math.PI; }
      else if (isLine(o)) {
        const seg = !o.visProp.straightfirst && !o.visProp.straightlast;
        const P = t => { const s = seg ? t : Math.tan(t); return [o.point1.X() + s * (o.point2.X() - o.point1.X()), o.point1.Y() + s * (o.point2.Y() - o.point1.Y())]; };
        X = t => P(t)[0]; Y = t => P(t)[1]; a = seg ? 0 : -Math.PI / 2 + 1e-4; z = seg ? 1 : Math.PI / 2 - 1e-4;
      } else return [];
      return [b.create('curve', [t => f(X(t), Y(t))[0], t => f(X(t), Y(t))[1], a, z], { strokeColor: c.warm, strokeWidth: 2, numberPointsHigh: 1600 })];
    };

    const NEED = { segment: 2, line: 2, ray: 2, circle: 2, circle3: 3, midpoint: 2, dist: 2, angle: 3, pbis: 2, abis: 3 };
    b.on('down', e => {
      if (mode === 'move') return;
      const pos = b.getMousePosition(e), uc = new JXG.Coords(JXG.COORDS_BY_SCREEN, pos, b).usrCoords.slice(1);
      const curveOrLine = o => isLine(o) || isCirc(o) || isCurve(o);
      const anyObj = o => isPt(o) || curveOrLine(o) || o.type === JXG.OBJECT_TYPE_POLYGON;

      if (mode === 'hide' || mode === 'label') {
        const o = hit(pos, anyObj); if (!o) return;
        if (mode === 'hide') o.setAttribute({ visible: false }); else o.setAttribute({ withLabel: !o.visProp.withlabel });
        refreshList(); return;
      }
      if (mode === 'intersect') {
        const o = hit(pos, curveOrLine); if (!o || picks.includes(o)) return;
        picks.push(o); if (picks.length < 2) return setStatus();
        const two = picks.some(x => !isLine(x));
        const io = i => b.create('intersection', [picks[0], picks[1], i], PT(nextName(), c.warm));
        return commit(two ? [io(0), io(1)] : [io(0)]);
      }
      if (['perp', 'parallel', 'tangent', 'reflectL', 'reflectP', 'rotate', 'dilate', 'invert'].includes(mode)) {
        const first = picks.length === 0;
        let o;
        if (mode === 'perp' || mode === 'parallel' || mode === 'tangent') o = first ? (hit(pos, isPt) || newPoint(uc, hit(pos, curveOrLine))) : hit(pos, mode === 'tangent' ? isCirc : isLine);
        else if (first) o = hit(pos, anyObj);
        else o = hit(pos, mode === 'reflectL' ? isLine : mode === 'invert' ? isCirc : isPt);
        if (!o) return setStatus();
        picks.push(o); if (picks.length < 2) return setStatus();
        const [x, y] = picks; let els = [];
        if (mode === 'perp') els = [b.create('perpendicular', [y, x], DERIVED)];
        if (mode === 'parallel') els = [b.create('parallel', [y, x], DERIVED)];
        if (mode === 'tangent') {
          const M = helper(() => (x.X() + y.center.X()) / 2, () => (x.Y() + y.center.Y()) / 2);
          const th = b.create('circle', [M, x], { visible: false }); th.gbHelper = true;
          const T1 = b.create('intersection', [y, th, 0], PT(nextName(), c.warm)), T2 = b.create('intersection', [y, th, 1], PT(nextName(), c.warm));
          els = [M, th, T1, T2, b.create('line', [x, T1], DERIVED), b.create('line', [x, T2], DERIVED)];
        }
        if (mode === 'reflectL') els = transform(x, reflectLineF(y));
        if (mode === 'reflectP') els = transform(x, reflectPtF(y));
        if (mode === 'rotate') { const d = ask('旋轉角度（度，逆時針為正）', '90'); if (d === null) { picks = []; return setStatus(); } els = transform(x, rotateF(y, d)); }
        if (mode === 'dilate') { const k = ask('位似倍數（可為負數或小數）', '2'); if (k === null) { picks = []; return setStatus(); } els = transform(x, dilateF(y, k)); }
        if (mode === 'invert') els = invert(x, y);
        return commit(els);
      }

      let created = null, p = hit(pos, isPt);
      if (!p) { created = newPoint(uc, hit(pos, curveOrLine)); p = created; }
      if (mode === 'point') return commit([created]);
      if (mode === 'circler') {
        const r = ask('半徑', '2'); if (r === null || r <= 0) return commit([created]);
        return commit([created, b.create('circle', [p, r], LINE)]);
      }
      if (mode === 'polygon') {
        if (picks.length >= 3 && p === picks[0]) { const made = picks.made || []; const poly = b.create('polygon', picks.slice(), { fillColor: c.accent, fillOpacity: 0.08, borders: LINE, vertices: { visible: true } }); return commit(made.concat([poly])); }
        if (picks.includes(p)) return; picks.push(p); if (created) (picks.made = picks.made || []).push(created); return setStatus();
      }
      if (picks.includes(p)) return; picks.push(p); if (created) (picks.made = picks.made || []).push(created);
      if (picks.length < NEED[mode]) return setStatus();
      const made = picks.made || [], [p1, p2, p3] = picks; let els = [];
      if (mode === 'segment') els = [b.create('segment', [p1, p2], LINE)];
      if (mode === 'line') els = [b.create('line', [p1, p2], DERIVED)];
      if (mode === 'ray') els = [b.create('line', [p1, p2], Object.assign({}, DERIVED, { straightFirst: false }))];
      if (mode === 'circle') els = [b.create('circle', [p1, p2], LINE)];
      if (mode === 'circle3') els = [b.create('circumcircle', [p1, p2, p3], Object.assign({}, LINE, { center: { visible: false } }))];
      if (mode === 'midpoint') els = [b.create('midpoint', [p1, p2], PT(nextName(), c.warm))];
      if (mode === 'pbis') { const M = b.create('midpoint', [p1, p2], { visible: false }), l = b.create('line', [p1, p2], { visible: false }); M.gbHelper = l.gbHelper = true; els = [M, l, b.create('perpendicular', [l, M], DERIVED)]; }
      if (mode === 'abis') els = [b.create('bisector', [p1, p2, p3], DERIVED)];
      if (mode === 'dist') els = [b.create('segment', [p1, p2], { strokeColor: c.muted, dash: 2, strokeWidth: 1 }), b.create('text', [() => (p1.X() + p2.X()) / 2, () => (p1.Y() + p2.Y()) / 2, () => p1.Dist(p2).toFixed(2)], { strokeColor: c.accent, fontSize: 14, anchorX: 'middle', anchorY: 'bottom' })];
      if (mode === 'angle') {
        const deg = () => { const ax = p1.X() - p2.X(), ay = p1.Y() - p2.Y(), bx = p3.X() - p2.X(), by = p3.Y() - p2.Y(); const v = Math.acos(Math.max(-1, Math.min(1, (ax * bx + ay * by) / (Math.hypot(ax, ay) * Math.hypot(bx, by))))) * 180 / Math.PI; return isFinite(v) ? v : 0; };
        const lab = k => { const ax = p1.X() - p2.X(), ay = p1.Y() - p2.Y(), bx = p3.X() - p2.X(), by = p3.Y() - p2.Y(); const la = Math.hypot(ax, ay) || 1, lb = Math.hypot(bx, by) || 1; const mx = ax / la + bx / lb, my = ay / la + by / lb, m = Math.hypot(mx, my) || 1, R = (b.getBoundingBox()[2] - b.getBoundingBox()[0]) / 9; return k === 0 ? p2.X() + mx / m * R : p2.Y() + my / m * R; };
        els = [b.create('nonreflexangle', [p1, p2, p3], { radius: () => (b.getBoundingBox()[2] - b.getBoundingBox()[0]) / 22, name: '', withLabel: false, strokeColor: c.accent, fillColor: c.accent, fillOpacity: 0.18 }),
               b.create('text', [() => lab(0), () => lab(1), () => deg().toFixed(1) + '°'], { strokeColor: c.accent, fontSize: 14, anchorX: 'middle', anchorY: 'middle' })];
      }
      commit(made.concat(els));
    });

    /* 物件清單（像代數區）：名稱、種類、數值，可勾選顯示 */
    const listEl = $('.gb-list');
    const KIND = o => isPt(o) ? '點' : isCirc(o) ? '圓' : isLine(o) ? (o.visProp.straightfirst || o.visProp.straightlast ? '直線' : '線段') : o.type === JXG.OBJECT_TYPE_POLYGON ? '多邊形' : isCurve(o) ? '曲線' : null;
    function refreshList() {
      if (listEl.hidden) return;
      const objs = hist.flat().filter(o => o && b.objects[o.id] && !o.gbHelper && KIND(o));
      listEl.innerHTML = objs.length ? `<ul>${objs.map(o => {
        const k = KIND(o), nm = isPt(o) ? o.name : isLine(o) && o.point1 ? `${o.point1.name}${o.point2.name}` : isCirc(o) && o.center && o.center.name ? `圓心 ${o.center.name}` : o.type === JXG.OBJECT_TYPE_POLYGON ? o.vertices.slice(0, -1).map(v => v.name).join('') : '';
        const val = isPt(o) ? `(${o.X().toFixed(2)}, ${o.Y().toFixed(2)})` : isCirc(o) ? `半徑 ${o.Radius().toFixed(2)}` : k === '線段' ? `長 ${o.L().toFixed(2)}` : '';
        return `<li><label><input type="checkbox" data-id="${o.id}"${o.visProp.visible !== false ? ' checked' : ''}> <b>${nm || '—'}</b> <span>${k}</span> <span class="v">${val}</span></label></li>`; }).join('')}</ul>` : '<p>還沒有物件。</p>';
    }
    listEl.addEventListener('change', e => { const o = b.objects[e.target.dataset.id]; if (o) o.setAttribute({ visible: e.target.checked }); });
    let lt = 0; b.on('update', () => { if (listEl.hidden) return; clearTimeout(lt); lt = setTimeout(refreshList, 150); });

    host.addEventListener('click', e => {
      const t = e.target.closest('button'); if (!t || !host.contains(t)) return;
      if (t.dataset.g !== undefined) { showTools(+t.dataset.g); const first = GROUPS[+t.dataset.g].tools[0][0]; setMode(first); }
      else if (t.dataset.m) setMode(t.dataset.m);
      else if (t.dataset.v === 'in') b.zoomIn(); else if (t.dataset.v === 'out') b.zoomOut(); else if (t.dataset.v === 'fit') fit();
      else if (t.dataset.a === 'undo') { const els = hist.pop(); if (els) els.slice().reverse().forEach(o => { try { b.removeObject(o); } catch (_) {} }); picks = []; setStatus(); refreshList(); }
      else if (t.dataset.a === 'clear') { if (!window.confirm('清除畫板上所有物件？')) return; hist.slice().reverse().forEach(els => els.slice().reverse().forEach(o => { try { b.removeObject(o); } catch (_) {} })); hist = []; picks = []; letter = 0; used.clear(); setStatus(); refreshList(); }
      else if (t.dataset.a === 'list') { listEl.hidden = !listEl.hidden; t.setAttribute('aria-expanded', !listEl.hidden); refreshList(); }
    });

    showTools(0); setStatus();
    if (spec) build(spec); else starter();

    function starter() {
      const A = newPoint([-3, -2]), B = newPoint([3, -2]), C = newPoint([0.6, 2.6]);
      hist.push([A, B, C, b.create('segment', [A, B], LINE), b.create('segment', [B, C], LINE), b.create('segment', [C, A], LINE)]);
    }

    /* 由解析好的 SVG 建圖：圓上的點變成可沿圓滑動的點、線段內的點沿線段滑動 */
    function build(sp) {
      const P = new Array(sp.points.length), made = [], segObj = new Array(sp.segs.length), circObj = new Array(sp.circles.length);
      sp.points.forEach(p => { if (p.name) used.add(p.name); });
      const mk = (i, host) => { const p = sp.points[i]; const o = host ? b.create('glider', [p.x, p.y, host], PT(p.name || '')) : b.create('point', [p.x, p.y], PT(p.name || '')); if (!p.name) o.setAttribute({ size: 2.5, withLabel: false }); P[i] = o; made.push(o); };
      for (let round = 0; round < 8; round++) {
        sp.points.forEach((p, i) => {
          if (P[i]) return;
          if (p.host == null) return mk(i);
          const h = p.host.kind === 'c' ? circObj[p.host.i] : segObj[p.host.i];
          if (h) mk(i, h);
        });
        sp.circles.forEach((ci, k) => {
          if (circObj[k]) return;
          const st = Object.assign({}, LINE, ci.dash ? { dash: 2 } : {}, ci.warm ? { strokeColor: c.warm } : {});
          if (ci.thru && ci.thru.length >= 3 && ci.thru.slice(0, 3).every(i => P[i])) circObj[k] = b.create('circumcircle', ci.thru.slice(0, 3).map(i => P[i]), Object.assign(st, { center: { visible: false } }));
          else if (ci.center != null && ci.thru && ci.thru.length && P[ci.center] && P[ci.thru[0]]) circObj[k] = b.create('circle', [P[ci.center], P[ci.thru[0]]], st);
          else if (ci.center != null && (!ci.thru || !ci.thru.length) && P[ci.center]) { const q = b.create('point', [ci.cx + ci.r, ci.cy], { size: 2, strokeColor: c.muted, fillColor: c.muted, withLabel: false, name: '' }); made.push(q); circObj[k] = b.create('circle', [P[ci.center], q], st); }
          else if (ci.center == null && (!ci.thru || ci.thru.length < 3)) { const o = b.create('point', [ci.cx, ci.cy], { visible: false, name: '' }); const q = b.create('point', [ci.cx + ci.r, ci.cy], { size: 2, strokeColor: c.muted, fillColor: c.muted, withLabel: false, name: '' }); made.push(o, q); circObj[k] = b.create('circle', [o, q], st); }
          if (circObj[k]) made.push(circObj[k]);
        });
        sp.segs.forEach((s, k) => {
          if (segObj[k] || !P[s.a] || !P[s.b]) return;
          segObj[k] = b.create('segment', [P[s.a], P[s.b]], Object.assign({}, LINE, s.dash ? { dash: 2, strokeWidth: 1.6 } : {}, s.warm ? { strokeColor: c.warm } : {}));
          made.push(segObj[k]);
        });
      }
      sp.points.forEach((p, i) => { if (!P[i]) mk(i); });
      sp.segs.forEach((s, k) => { if (!segObj[k] && P[s.a] && P[s.b]) made.push(b.create('segment', [P[s.a], P[s.b]], LINE)); });
      hist.push(made);
    }

    return { board: b, destroy() { try { if (ro) ro.disconnect(); JXG.JSXGraph.freeBoard(b); } catch (_) {} host.innerHTML = ''; host.classList.remove('gb'); } };
  }

  /* ---------- SVG 附圖解析 ---------- */
  const LABEL = /^[A-Z][′'’″]*[0-9₀-₉]?[′'’]*$|^[A-Z]_?[0-9]$/;
  function parseSVG(svg) {
    const vb = (svg.getAttribute('viewBox') || '0 0 320 220').split(/[\s,]+/).map(Number);
    const vt = [], segRaw = [], circRaw = [], labels = [];
    const attr = (el, k) => { for (let e = el; e && e !== svg.parentNode; e = e.parentNode) { const v = e.getAttribute && e.getAttribute(k); if (v != null) return v; } return null; };
    const dashed = el => { const d = attr(el, 'stroke-dasharray'); return !!d && d !== 'none'; };
    const warm = el => { const s = attr(el, 'stroke'); return !!s && s !== 'currentColor' && s !== 'none' && !/^#?0+$|black/i.test(s); };
    const num = (el, k) => parseFloat(el.getAttribute(k) || '0');
    const addSeg = (x1, y1, x2, y2, el) => { if (Math.hypot(x2 - x1, y2 - y1) < 12) return; segRaw.push({ x1, y1, x2, y2, dash: dashed(el), warm: warm(el) }); };
    const offset = el => { let dx = 0, dy = 0; for (let e = el; e && e !== svg; e = e.parentNode) { const t = e.getAttribute && e.getAttribute('transform'); const m = t && /translate\(\s*([-\d.]+)[\s,]*([-\d.]+)?\s*\)/.exec(t); if (m) { dx += +m[1]; dy += +(m[2] || 0); } } return [dx, dy]; };
    svg.querySelectorAll('line').forEach(el => { const [dx, dy] = offset(el); addSeg(num(el, 'x1') + dx, num(el, 'y1') + dy, num(el, 'x2') + dx, num(el, 'y2') + dy, el); });
    svg.querySelectorAll('polygon, polyline').forEach(el => {
      const [dx, dy] = offset(el), ps = (el.getAttribute('points') || '').trim().split(/[\s,]+/).map(Number), pts = [];
      for (let i = 0; i + 1 < ps.length; i += 2) pts.push([ps[i] + dx, ps[i + 1] + dy]);
      if (pts.length > 8) return;  // 折線很多點多半是函數圖形，不匯入
      let len = 0; for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      if (len < 30) return;        // 直角記號等小標記
      for (let i = 1; i < pts.length; i++) addSeg(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], el);
      if (el.tagName.toLowerCase() === 'polygon' && pts.length > 2) addSeg(pts[pts.length - 1][0], pts[pts.length - 1][1], pts[0][0], pts[0][1], el);
    });
    svg.querySelectorAll('path').forEach(el => {
      const d = el.getAttribute('d') || ''; if (/[AaCcQqSsTt]/.test(d)) return;
      const [dx, dy] = offset(el), tk = d.match(/[MmLlHhVvZz]|-?[\d.]+(?:e-?\d+)?/g) || [];
      let i = 0, cmd = 'M', x = 0, y = 0, sx = 0, sy = 0; const nx = () => parseFloat(tk[i++]);
      while (i < tk.length) {
        if (/[A-Za-z]/.test(tk[i])) cmd = tk[i++];
        if (cmd === 'Z' || cmd === 'z') { addSeg(x + dx, y + dy, sx + dx, sy + dy, el); x = sx; y = sy; continue; }
        let X = x, Y = y;
        if (cmd === 'M' || cmd === 'L') { X = nx(); Y = nx(); } else if (cmd === 'm' || cmd === 'l') { X = x + nx(); Y = y + nx(); }
        else if (cmd === 'H') X = nx(); else if (cmd === 'h') X = x + nx(); else if (cmd === 'V') Y = nx(); else if (cmd === 'v') Y = y + nx();
        else { i++; continue; }
        if (cmd === 'M' || cmd === 'm') { sx = X; sy = Y; cmd = cmd === 'M' ? 'L' : 'l'; } else addSeg(x + dx, y + dy, X + dx, Y + dy, el);
        x = X; y = Y;
      }
    });
    svg.querySelectorAll('circle, ellipse').forEach(el => {
      const [dx, dy] = offset(el), cx = num(el, 'cx') + dx, cy = num(el, 'cy') + dy, r = el.tagName.toLowerCase() === 'circle' ? num(el, 'r') : (num(el, 'rx') + num(el, 'ry')) / 2;
      if (r <= 4.5) vt.push([cx, cy, true]); else circRaw.push({ cx, cy, r, dash: dashed(el), warm: warm(el) });
    });
    svg.querySelectorAll('text').forEach(el => {
      const s = (el.textContent || '').trim(); if (!LABEL.test(s)) return;
      const [dx, dy] = offset(el), x = num(el, 'x') + dx, y = num(el, 'y') + dy, fs = parseFloat(attr(el, 'font-size') || '14'), anc = attr(el, 'text-anchor') || 'start';
      const w = fs * 0.6 * s.length, cx = anc === 'middle' ? x : anc === 'end' ? x - w / 2 : x + w / 2;
      labels.push({ s, x: cx, y: y - fs * 0.35 });
    });
    segRaw.forEach(s => { vt.push([s.x1, s.y1]); vt.push([s.x2, s.y2]); });

    // 合併相近的頂點
    const pts = [];
    const find = (x, y, tol) => pts.findIndex(p => Math.hypot(p.x - x, p.y - y) <= tol);
    vt.forEach(([x, y]) => { if (find(x, y, 3) < 0) pts.push({ x, y, name: '' }); });
    // 名稱：每個標籤配最近的頂點
    labels.sort((a, b) => a.s.localeCompare(b.s));
    labels.forEach(l => {
      let best = -1, bd = 30; pts.forEach((p, i) => { if (p.name) return; const d = Math.hypot(p.x - l.x, p.y - l.y); if (d < bd) { bd = d; best = i; } });
      if (best >= 0) pts[best].name = l.s;
      else circRaw.forEach(ci => { if (Math.hypot(ci.cx - l.x, ci.cy - l.y) < 26 && find(ci.cx, ci.cy, 3) < 0) pts.push({ x: ci.cx, y: ci.cy, name: l.s }); });
    });
    const segs = []; segRaw.forEach(s => { const a = find(s.x1, s.y1, 3), b2 = find(s.x2, s.y2, 3); if (a >= 0 && b2 >= 0 && a !== b2 && !segs.some(t => (t.a === a && t.b === b2) || (t.a === b2 && t.b === a))) segs.push({ a, b: b2, dash: s.dash, warm: s.warm }); });
    // 圓：找圓心與圓上的點
    const circles = circRaw.map(ci => {
      const on = pts.map((p, i) => [i, Math.abs(Math.hypot(p.x - ci.cx, p.y - ci.cy) - ci.r)]).filter(([, d]) => d < 3).map(([i]) => i);
      on.sort((i, j) => (pts[j].name ? 1 : 0) - (pts[i].name ? 1 : 0));
      const center = find(ci.cx, ci.cy, 3);
      return Object.assign({}, ci, { thru: on, center: center >= 0 ? center : null });
    });
    // 依附：圓上多出來的點沿圓滑動；落在線段內部的點沿線段滑動
    const usedDef = new Set(); circles.forEach(ci => (ci.thru.length >= 3 ? ci.thru.slice(0, 3) : ci.thru.slice(0, 1)).forEach(i => usedDef.add(i)));
    circles.forEach((ci, k) => { const def = ci.thru.length >= 3 ? 3 : (ci.center != null ? 1 : 0); ci.thru.slice(def).forEach(i => { if (pts[i].host == null && !usedDef.has(i)) pts[i].host = { kind: 'c', i: k }; }); });
    pts.forEach((p, i) => {
      if (p.host != null || usedDef.has(i)) return;
      segs.forEach((s, k) => {
        if (p.host != null || s.a === i || s.b === i) return;
        const A = pts[s.a], B = pts[s.b], L = Math.hypot(B.x - A.x, B.y - A.y), t = ((p.x - A.x) * (B.x - A.x) + (p.y - A.y) * (B.y - A.y)) / (L * L);
        if (t <= 0.02 || t >= 0.98) return;
        const d = Math.abs((B.x - A.x) * (A.y - p.y) - (A.x - p.x) * (B.y - A.y)) / L;
        const onSeg = q => q.host && q.host.kind === 's';
        if (d < 2.5 && !onSeg(pts[s.a]) && !onSeg(pts[s.b])) p.host = { kind: 's', i: k };
      });
    });
    // 座標：SVG 寬度對應 10 個單位，y 軸翻轉
    const sc = 10 / (vb[2] || 320), X = x => (x - vb[0]) * sc - 5, Y = y => -(y - vb[1]) * sc + (vb[3] || 220) * sc / 2;
    pts.forEach(p => { p.x = X(p.x); p.y = Y(p.y); });
    circles.forEach(ci => { ci.cx = X(ci.cx); ci.cy = Y(ci.cy); ci.r *= sc; });
    const h = (vb[3] || 220) * sc / 2, pad = 0.8;
    return { points: pts, segs, circles, bbox: [-5 - pad, h + pad, 5 + pad, -h - pad] };
  }

  /* 適合匯入的圖：至少兩個大寫字母標籤，而且有線段或圓 */
  function importable(svg) {
    const n = [...svg.querySelectorAll('text')].filter(t => LABEL.test((t.textContent || '').trim())).length;
    if (n < 2 || !svg.querySelector('line, polygon, polyline, path, circle')) return false;
    try { const sp = parseSVG(svg); return sp.segs.length + sp.circles.length > 0 && sp.points.some(p => p.name); } catch (_) { return false; }
  }

  window.GeoBoard = { mount, importable, parseSVG };
})();
