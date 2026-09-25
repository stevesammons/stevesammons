/* Interactive Bible map engine for stevesammons.com.
   BibleMap(rootElement, config) renders a story map: chapters, places with confidence
   levels, animated routes, shaded terrain, facts and a place card. No dependencies. */
(function () {
  if (window.BibleMap) return;
  var NS = 'http://www.w3.org/2000/svg';
  var CSS = [
    '.bm{--ink:#1f2a2c;--muted:#5d6a6d;--line:#d9d4c4;--paper:#fbf8ef;--sea:#c9dde1;--seaInk:#4a7079;--accent:#c8322d;--accent2:#8a5a14;--ref:#3b4a4d;font-family:inherit;color:var(--ink);line-height:1.55;margin:28px 0;border:1px solid var(--line);background:var(--paper);border-radius:6px;overflow:hidden;overflow:clip;text-align:left}',
    '.bm *{box-sizing:border-box}',
    '.bm button{font:inherit;cursor:pointer;background:none;border:0;color:inherit;margin:0;padding:0;letter-spacing:normal;text-transform:none;line-height:inherit;box-shadow:none;min-height:0}',
    '.bm button:focus-visible,.bm a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}',
    '.bm-head{padding:16px 18px 10px;border-bottom:1px solid var(--line)}',
    '.bm-kicker{font-size:.72em;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700}',
    '.bm-title{font-size:1.15em;font-weight:700;margin:2px 0 10px;color:var(--ink);line-height:1.3}',
    '.bm-tabs{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;scrollbar-width:thin;-webkit-overflow-scrolling:touch}',
    '.bm .bm-tab{flex:0 0 auto;display:flex;align-items:center;gap:7px;padding:6px 11px 6px 7px!important;border:1px solid var(--line)!important;border-radius:999px;background:#fff!important;font-size:.86em;color:var(--muted)!important;white-space:nowrap;transition:background .15s,color .15s,border-color .15s}',
    '.bm .bm-tab b{display:inline-grid;place-items:center;width:21px;height:21px;border-radius:50%;background:#efe6cf;color:var(--ink);font-size:.8em}',
    '.bm .bm-tab:hover{border-color:var(--accent)!important;color:var(--ink)!important}',
    '.bm .bm-tab[aria-selected="true"]{background:var(--ink)!important;border-color:var(--ink)!important;color:#fff!important}',
    '.bm .bm-tab[aria-selected="true"] b{background:var(--accent);color:#fff}',
    '.bm-body{display:grid;grid-template-columns:1fr}',
    '@media (min-width:760px){.bm-body{grid-template-columns:minmax(0,1.3fr) minmax(0,1fr)}.bm-panel{border-left:1px solid var(--line)}.bm-mapcol{position:sticky;top:72px;align-self:start}}',
    '.bm-mapwrap{position:relative;background:var(--sea);overflow:hidden}',
    '.bm svg.bm-map{display:block;width:100%;height:auto;touch-action:manipulation;user-select:none}',
    '.bm-map text{font-family:inherit;pointer-events:none}',
    '.bm-water{fill:var(--seaInk);font-style:italic;letter-spacing:.14em;text-transform:uppercase}',
    '.bm-region{fill:#6f5f3c;font-style:italic;letter-spacing:.16em;text-transform:uppercase;opacity:.8}',
    '.bm-rivlabel{fill:#3f6f79;font-style:italic;letter-spacing:.05em}',
    '.bm-country{fill:#6b5d45;font-weight:700;letter-spacing:.22em;text-transform:uppercase;opacity:.8;pointer-events:none}',
    '.bm-halo{paint-order:stroke;stroke:rgba(251,248,239,.85);stroke-linejoin:round}',
    '.bm-route{fill:none;stroke:var(--accent);stroke-linecap:round;stroke-linejoin:round;opacity:0;transition:opacity .45s}',
    '.bm-route.on{opacity:1}',
    '.bm-route.dash{stroke-dasharray:1 6}',
    '.bm-route.req{stroke:var(--accent2)}',
    '.bm-route.draw{animation:bmDraw 1.5s ease-out forwards}',
    '@keyframes bmDraw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}',
    '.bm-pl{cursor:pointer;transition:opacity .3s}',
    '.bm-pl .dot{stroke:#fff}',
    '.bm-pl .halo{fill:var(--accent);opacity:0}',
    '.bm-pl.hot .halo{animation:bmPulse 2.2s ease-in-out infinite}',
    '.bm-pl.dim{opacity:.5}',
    '.bm-pl.sel .dot{stroke:var(--ink)}',
    '.bm-pl .lbl{font-weight:700;fill:var(--ink)}',
    '.bm-pl .sub{fill:var(--muted)}',
    '.bm-pl.ref .lbl{font-weight:600;fill:var(--ref)}',
    '.bm-pl:focus{outline:none}.bm-pl:focus-visible .dot{stroke:var(--accent)}',
    '.bm-area{fill:var(--accent2);fill-opacity:.13;stroke:var(--accent2);stroke-opacity:.8}',
    '.bm-pl.hot .bm-area{fill-opacity:.2}',
    '@keyframes bmPulse{0%,100%{opacity:.1}50%{opacity:.3}}',
    '.bm-hidden{display:none}',
    '.bm-tools{display:flex;gap:6px;flex-wrap:wrap;align-items:center;padding:8px 10px;border-top:1px solid var(--line);background:var(--paper)}',
    '.bm-tools span{font-size:.74em;color:var(--muted);margin-right:2px}',
    '.bm .bm-chip{font-size:.74em;background:#fff!important;border:1px solid var(--line)!important;border-radius:999px;padding:4px 10px!important;color:var(--ink)!important}',
    '.bm .bm-chip[aria-pressed="true"]{background:var(--ink)!important;color:#fff!important;border-color:var(--ink)!important}',
    '.bm-panel{padding:18px 18px 16px;display:flex;flex-direction:column;gap:14px;min-width:0}',
    '.bm-step{font-size:.72em;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:700}',
    '.bm-ch{font-size:1.2em;font-weight:700;margin:2px 0 4px;color:var(--ink);line-height:1.3}',
    '.bm-meta{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}',
    '.bm-badge{font-size:.74em;border-radius:4px;padding:2px 8px;background:#efe6cf;color:var(--ink)}',
    '.bm-text p{margin:0 0 .7em;font-size:.95em;color:#3a4547}',
    '.bm-text p:last-child{margin-bottom:0}',
    '.bm-quote{border-left:3px solid var(--accent);padding:4px 0 4px 12px;margin:10px 0;font-style:italic;color:var(--ink);font-size:.95em}',
    '.bm-quote small{display:block;font-style:normal;color:var(--muted);font-size:.8em;margin-top:2px}',
    '.bm-facts{background:#fff;border:1px solid var(--line);border-radius:6px;padding:10px 14px 10px 14px;margin-top:10px}',
    '.bm-facts b{display:block;font-size:.7em;letter-spacing:.12em;text-transform:uppercase;color:var(--accent2);margin-bottom:4px}',
    '.bm-facts ul{margin:0;padding-left:18px}',
    '.bm-facts li{font-size:.88em;color:#3a4547;margin:3px 0}',
    '.bm-refs{font-size:.82em;color:var(--muted)}',
    '.bm-refs a{color:var(--accent);text-decoration:underline;text-underline-offset:2px}',
    '.bm-nav{display:flex;justify-content:space-between;gap:8px;margin-top:auto;padding-top:6px}',
    '.bm .bm-btn{border:1px solid var(--ink)!important;border-radius:4px;padding:7px 14px!important;font-size:.85em;font-weight:600;background:#fff!important;color:var(--ink)!important}',
    '.bm .bm-btn.pri{background:var(--ink)!important;color:#fff!important}',
    '.bm .bm-btn:disabled{opacity:.35;cursor:default}',
    '.bm-card{border:1px solid var(--line);background:#fff;border-radius:6px;padding:12px 14px}',
    '.bm-card-h{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap}',
    '.bm-card-t{font-weight:700;font-size:1em}',
    '.bm-card-t span{font-weight:400;color:var(--muted)}',
    '.bm-conf{font-size:.7em;letter-spacing:.06em;text-transform:uppercase;font-weight:700;padding:2px 7px;border-radius:3px;white-space:nowrap}',
    '.bm-c-secure{background:#e2efe4;color:#2d6a3a}.bm-c-probable{background:#f5ecd6;color:#81601a}.bm-c-debated{background:#f7e1dc;color:#9a3b2b}.bm-c-modern{background:#e6ebec;color:#3b4a4d}',
    '.bm-card p{margin:.45em 0 0;font-size:.88em;color:#3a4547}',
    '.bm-card .bm-stats{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.8em;color:var(--muted);margin-top:.55em}',
    '.bm-foot{border-top:1px solid var(--line);padding:10px 18px;font-size:.78em;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 16px;align-items:center}',
    '.bm-key{display:inline-flex;align-items:center;gap:6px}',
    '.bm-key i{display:inline-block;width:10px;height:10px;border-radius:50%}',
    '@media (prefers-reduced-motion:reduce){.bm *{animation:none!important;transition:none!important}}'
  ].join('\n');

  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function h(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function miles(a, b) {
    var R = 3958.8, r = Math.PI / 180, dl = (b[0] - a[0]) * r, dn = (b[1] - a[1]) * r;
    var x = Math.sin(dl / 2) * Math.sin(dl / 2) + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dn / 2) * Math.sin(dn / 2);
    return 2 * R * Math.asin(Math.sqrt(x));
  }
  function fmt(n) { return Math.round(n).toLocaleString('en-US'); }
  function bg(q) { return 'https://www.biblegateway.com/passage/?search=' + encodeURIComponent(q) + '&version=NIV'; }
  var CONF = { secure: 'Secure identification', probable: 'Probable identification', debated: 'Location debated', modern: 'Modern reference', unknown: 'Location unknown', region: 'Approximate region' };

  window.BibleMap = function (root, C) {
    if (!document.getElementById('bm-css')) { var st = document.createElement('style'); st.id = 'bm-css'; st.textContent = CSS; document.head.appendChild(st); }
    var uid = 'bm' + Math.random().toString(36).slice(2, 7);
    root.classList.add('bm');
    root.innerHTML = '';
    var W = C.W, H = C.H, bb = C.bbox, K = C.k, SX = C.sx;
    function P(lat, lon) { return [(lon - bb[0]) * K * SX, (bb[3] - lat) * SX]; }
    function smooth(pts) {
      var q = pts.map(function (p) { return P(p[0], p[1]); }), d = 'M' + q[0][0].toFixed(1) + ' ' + q[0][1].toFixed(1);
      for (var i = 0; i < q.length - 1; i++) {
        var p0 = q[i - 1] || q[i], p1 = q[i], p2 = q[i + 1], p3 = q[i + 2] || p2;
        d += ' C' + (p1[0] + (p2[0] - p0[0]) / 6).toFixed(1) + ' ' + (p1[1] + (p2[1] - p0[1]) / 6).toFixed(1) + ' ' +
          (p2[0] - (p3[0] - p1[0]) / 6).toFixed(1) + ' ' + (p2[1] - (p3[1] - p1[1]) / 6).toFixed(1) + ' ' + p2[0].toFixed(1) + ' ' + p2[1].toFixed(1);
      }
      return d;
    }

    /* ---------- layout ---------- */
    var head = h('div', 'bm-head', '<div class="bm-kicker">' + esc(C.kicker || 'Interactive map') + '</div><div class="bm-title">' + esc(C.title) + '</div>');
    var tabs = h('div', 'bm-tabs'); tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', 'Chapters of the story');
    head.appendChild(tabs); root.appendChild(head);
    var body = h('div', 'bm-body'); root.appendChild(body);
    var mapcol = h('div', 'bm-mapcol'); body.appendChild(mapcol);
    var wrap = h('div', 'bm-mapwrap'); mapcol.appendChild(wrap);
    var svg = el('svg', { 'class': 'bm-map', viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': C.mapLabel || ('Map for ' + C.title) });
    wrap.appendChild(svg);
    var tools = h('div', 'bm-tools', '<span>Show:</span>'); mapcol.appendChild(tools);
    var panel = h('div', 'bm-panel'); body.appendChild(panel);
    var live = h('div'); live.setAttribute('aria-live', 'polite'); panel.appendChild(live);
    var card = h('div', 'bm-card'); card.setAttribute('aria-live', 'polite'); panel.appendChild(card);
    var refs = h('div', 'bm-refs'); panel.appendChild(refs);
    var nav = h('div', 'bm-nav', '<button type="button" class="bm-btn" data-go="-1">&larr; Previous</button><button type="button" class="bm-btn pri" data-go="1">Next &rarr;</button>');
    panel.appendChild(nav);
    var foot = h('div', 'bm-foot',
      '<span class="bm-key"><i style="background:var(--accent)"></i>Story location</span>' +
      '<span class="bm-key"><i style="background:var(--ref)"></i>Modern reference</span>' +
      '<span class="bm-key"><i style="background:var(--accent2);border-radius:2px;opacity:.6"></i>Approximate area</span>' +
      '<span>' + esc(C.note || 'Routes are illustrative, not surveyed paths. Modern borders are shown only for orientation.') + '</span>' +
      '<span>Map data: Natural Earth; terrain: Mapzen/AWS Terrain Tiles (SRTM and others).</span>');
    root.appendChild(foot);

    /* ---------- base map ---------- */
    var defs = el('defs', {}, svg);
    var clip = el('clipPath', { id: uid + 'land' }, defs); el('path', { d: C.land }, clip);
    el('rect', { x: -W, y: -H, width: W * 3, height: H * 3, fill: 'var(--sea)' }, svg);
    var gTerrain = el('g', {}, svg);
    el('path', { d: C.land, fill: '#ebe3cc' }, gTerrain);
    if (C.relief) el('image', { href: C.relief, x: 0, y: 0, width: W, height: H, preserveAspectRatio: 'none', 'clip-path': 'url(#' + uid + 'land)' }, gTerrain);
    var gFlat = el('g', { 'class': 'bm-hidden' }, svg);
    el('path', { d: C.land, fill: '#efe7d2' }, gFlat);
    el('path', { d: C.land, fill: 'none', stroke: '#8fb0b6', 'stroke-width': 'calc(1px*var(--k))' }, svg);
    var gBorders = el('g', { 'class': 'bm-borders' }, svg);
    (C.borders || []).forEach(function (d) { el('path', { d: d, fill: 'none', stroke: '#6b5d45', 'stroke-opacity': '.55', 'stroke-width': 'calc(1px*var(--k))', 'stroke-dasharray': 'calc(4px*var(--k)) calc(3px*var(--k))' }, gBorders); });
    var gWater = el('g', {}, svg);
    (C.rivers || []).forEach(function (r) { el('path', { d: r.d, fill: 'none', stroke: '#6f9fa9', 'stroke-width': 'calc(' + (r.rank <= 4 ? 1.8 : 1.3) + 'px*var(--k))', 'stroke-dasharray': r.int ? 'calc(3px*var(--k)) calc(2px*var(--k))' : null, 'stroke-linecap': 'round' }, gWater); });
    (C.lakes || []).forEach(function (l) { el('path', { d: l.d, fill: 'var(--sea)', stroke: '#8fb0b6', 'stroke-width': 'calc(1px*var(--k))' }, gWater); });

    var gLabels = el('g', {}, svg), gRegionLabels = el('g', {}, gLabels);
    (C.labels || []).forEach(function (L) {
      var q = P(L.ll[0], L.ll[1]);
      var cls = L.kind === 'water' ? 'bm-water' : L.kind === 'river' ? 'bm-rivlabel bm-halo' : 'bm-region bm-halo';
      var t = el('text', { x: q[0], y: q[1], 'class': cls, 'text-anchor': 'middle', transform: L.rot ? 'rotate(' + L.rot + ' ' + q[0] + ' ' + q[1] + ')' : null,
        style: 'font-size:calc(' + (L.size || (L.kind === 'water' ? 12 : L.kind === 'river' ? 10.5 : 10.5)) + 'px*var(--k));stroke-width:calc(3px*var(--k))' }, L.kind === 'region' ? gRegionLabels : gLabels);
      t.textContent = L.t;
    });

    // Modern country names, shown with the modern borders. C.countries = [{t, pts: [x, y, d, ...]}]:
    // candidate points inside the country, d = distance to its border (map units).
    var gCountries = el('g', { 'class': 'bm-countries' }, svg), cEls = [];
    (C.countries || []).forEach(function (c) {
      var t = el('text', { 'class': 'bm-country bm-halo', 'text-anchor': 'middle', x: 0, y: 0,
        style: 'font-size:calc(' + (c.size || 11) + 'px*var(--k));stroke-width:calc(3px*var(--k))' }, gCountries);
      t.textContent = c.t;
      var pts = [];
      for (var i = 0; i + 2 < c.pts.length; i += 3) pts.push([c.pts[i], c.pts[i + 1], c.pts[i + 2]]);
      cEls.push({ t: t, pts: pts, size: c.size || 11 });
    });

    var gRoutes = el('g', {}, svg), routeEls = {};
    Object.keys(C.routes || {}).forEach(function (k) {
      var R = C.routes[k];
      routeEls[k] = el('path', { d: smooth(R.pts), 'class': 'bm-route ' + (R.style || ''), style: 'stroke-width:calc(3px*var(--k))' }, gRoutes);
    });

    var gPlaces = el('g', {}, svg), plEls = {}, order = [], circles = [];
    var PL = C.places;
    Object.keys(PL).forEach(function (k) {
      var p = PL[k], q = P(p.ll[0], p.ll[1]);
      var g = el('g', { 'class': 'bm-pl' + (p.kind === 'ref' ? ' ref' : ''), tabindex: '0', role: 'button', 'aria-label': p.name + (p.sub ? ', ' + p.sub : '') + '. ' + (p.confT || CONF[p.conf] || '') }, gPlaces);
      if (p.area) {
        var rx = p.area[0] / (111.32 * Math.cos(p.ll[0] * Math.PI / 180)) * K * SX, ry = p.area[1] / 110.57 * SX;
        el('ellipse', { cx: q[0], cy: q[1], rx: rx, ry: ry, 'class': 'bm-area', style: 'stroke-width:calc(1.5px*var(--k));stroke-dasharray:calc(4px*var(--k)) calc(3px*var(--k))' }, g);
      }
      var r0 = p.kind === 'ref' ? 4.5 : p.main ? 7.5 : 6;
      circles.push([el('circle', { cx: q[0], cy: q[1], 'class': 'halo', r: 15 }, g), 15]);
      circles.push([el('circle', { cx: q[0], cy: q[1], 'class': 'dot', r: r0, fill: p.kind === 'ref' ? 'var(--ref)' : p.area ? 'var(--accent2)' : 'var(--accent)', style: 'stroke-width:calc(2.2px*var(--k))' }, g), r0]);
      var lbl = el('text', { 'class': 'lbl bm-halo', style: 'font-size:calc(' + (p.main ? 14.5 : p.kind === 'ref' ? 12 : 13.5) + 'px*var(--k));stroke-width:calc(3.5px*var(--k))' }, g); lbl.textContent = p.name;
      var sub = null;
      if (p.sub) { sub = el('text', { 'class': 'sub bm-halo', style: 'font-size:calc(10.5px*var(--k));stroke-width:calc(3px*var(--k))' }, g); sub.textContent = p.sub; }
      var t = el('title', {}, g); t.textContent = p.name;
      g.addEventListener('click', function () { select(k); });
      g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(k); } });
      plEls[k] = { g: g, lbl: lbl, sub: sub, q: q, r: r0 };
      order.push(k);
    });

    // Scale bar and north arrow live in screen space (outside the zoomable view).
    var gUI = el('g', {}, svg);
    var sb = el('g', {}, gUI), na = el('g', {}, gUI);

    /* ---------- toggles ---------- */
    var toggles = [['terrain', 'Terrain', true], ['borders', 'Modern borders', true]];
    if (order.some(function (k) { return PL[k].kind === 'ref'; })) toggles.push(['modern', 'Modern towns', true]);
    toggles.forEach(function (t) {
      var b = h('button', 'bm-chip', t[1]); b.type = 'button'; b.setAttribute('aria-pressed', 'true');
      b.addEventListener('click', function () {
        var on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', on);
        if (t[0] === 'terrain') { gTerrain.classList.toggle('bm-hidden', !on); gFlat.classList.toggle('bm-hidden', on); }
        if (t[0] === 'borders') { gBorders.classList.toggle('bm-hidden', !on); gCountries.classList.toggle('bm-hidden', !on); }
        if (t[0] === 'modern') order.forEach(function (k) { if (PL[k].kind === 'ref') plEls[k].g.classList.toggle('bm-hidden', !on); });
        layoutLabels();
      });
      tools.appendChild(b);
    });

    /* ---------- view (zoom) ---------- */
    var view = [0, 0, W, H], anim = null;
    function viewFor(ch) {
      if (!ch || !ch.view) return [0, 0, W, H];
      var a = P(ch.view[3], ch.view[0]), b = P(ch.view[1], ch.view[2]);
      var vw = b[0] - a[0], vh = b[1] - a[1], cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2;
      var ar = H / W; if (vh / vw > ar) vw = vh / ar; else vh = vw * ar;
      return [cx - vw / 2, cy - vh / 2, vw, vh];
    }
    function setView(v) {
      view = v;
      svg.setAttribute('viewBox', v.map(function (n) { return n.toFixed(2); }).join(' '));
      scale();
    }
    function animateTo(v) {
      if (anim) cancelAnimationFrame(anim);
      var from = view.slice(), t0 = null, reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (reduce) { setView(v); layoutLabels(); return; }
      function step(ts) {
        if (!t0) t0 = ts; var t = Math.min(1, (ts - t0) / 700), e = t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        setView(from.map(function (f, i) { return f + (v[i] - f) * e; }));
        if (t < 1) anim = requestAnimationFrame(step); else { anim = null; layoutLabels(); }
      }
      anim = requestAnimationFrame(step);
    }
    function scale() {
      var px = svg.getBoundingClientRect().width || W;
      var k = view[2] / px;
      svg.style.setProperty('--k', k.toFixed(4));
      circles.forEach(function (c) { c[0].setAttribute('r', (c[1] * k).toFixed(2)); });
      drawUI(k);
    }
    function drawUI(k) {
      // scale bar
      while (sb.firstChild) sb.removeChild(sb.firstChild);
      var mpu = 1 / SX * 69.05; // miles per SVG unit (latitude degrees)
      var target = view[2] * 0.22 * mpu, nice = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000];
      var m = nice[0]; nice.forEach(function (n) { if (n <= target) m = n; });
      var len = m / mpu, x0 = view[0] + view[2] - len - 16 * k, y0 = view[1] + view[3] - 16 * k;
      el('rect', { x: x0 - 6 * k, y: y0 - 16 * k, width: len + 12 * k, height: 26 * k, rx: 3 * k, fill: 'rgba(251,248,239,.8)' }, sb);
      el('rect', { x: x0, y: y0 - 6 * k, width: len / 2, height: 4 * k, fill: 'var(--ink)' }, sb);
      el('rect', { x: x0 + len / 2, y: y0 - 6 * k, width: len / 2, height: 4 * k, fill: '#fff', stroke: 'var(--ink)', 'stroke-width': .8 * k }, sb);
      var t = el('text', { x: x0 + len / 2, y: y0 + 7 * k, 'text-anchor': 'middle', style: 'font-size:' + (10 * k) + 'px', fill: 'var(--ink)' }, sb);
      t.textContent = fmt(m) + ' mi (' + fmt(m * 1.609) + ' km)';
      // north arrow
      while (na.firstChild) na.removeChild(na.firstChild);
      var ax = view[0] + 22 * k, ay = view[1] + 26 * k;
      el('circle', { cx: ax, cy: ay + 2 * k, r: 15 * k, fill: 'rgba(251,248,239,.8)' }, na);
      el('path', { d: 'M' + ax + ' ' + (ay - 10 * k) + ' L' + (ax + 6 * k) + ' ' + (ay + 7 * k) + ' L' + ax + ' ' + (ay + 3 * k) + ' L' + (ax - 6 * k) + ' ' + (ay + 7 * k) + ' Z', fill: 'var(--ink)' }, na);
      var nt = el('text', { x: ax, y: ay + 16 * k, 'text-anchor': 'middle', style: 'font-size:' + (8 * k) + 'px;font-weight:700', fill: 'var(--ink)' }, na); nt.textContent = 'N';
    }

    /* ---------- label placement ---------- */
    function layoutLabels() {
      var k = parseFloat(svg.style.getPropertyValue('--k')) || 1, boxes = [];
      function hit(b) { for (var i = 0; i < boxes.length; i++) { var o = boxes[i]; if (b.x < o.x + o.w && b.x + b.w > o.x && b.y < o.y + o.h && b.y + b.h > o.y) return true; } return false; }
      var pri = order.slice().sort(function (a, b) {
        function s(x) { var p = PL[x], e = plEls[x]; return (e.g.classList.contains('hot') ? 0 : 2) + (p.kind === 'ref' ? 1 : 0) - (p.main ? 1 : 0); }
        return s(a) - s(b);
      });
      pri.forEach(function (key) { var e = plEls[key]; if (!e.g.classList.contains('bm-hidden')) boxes.push({ x: e.q[0] - e.r * k, y: e.q[1] - e.r * k, w: 2 * e.r * k, h: 2 * e.r * k }); });
      pri.forEach(function (key) {
        var e = plEls[key], p = PL[key];
        if (e.g.classList.contains('bm-hidden')) return;
        var lb = e.lbl.getBBox(), sw = e.sub ? e.sub.getBBox().width : 0, tw = Math.max(lb.width, sw), th = lb.height + (e.sub ? 12 * k : 0);
        var gap = (e.r + 5) * k, cands = { r: [gap, 0, 'start'], l: [-gap, 0, 'end'], t: [0, -gap - th + 9 * k, 'middle'], b: [0, gap + 10 * k, 'middle'], tr: [gap * .8, -gap, 'start'], br: [gap * .8, gap, 'start'], tl: [-gap * .8, -gap, 'end'], bl: [-gap * .8, gap, 'end'] };
        var prefs = (p.label ? [p.label] : []).concat(['r', 'l', 'tr', 'br', 't', 'b', 'tl', 'bl']), chosen = null, fb = null;
        for (var i = 0; i < prefs.length; i++) {
          var c = cands[prefs[i]]; if (!c) continue;
          var x = e.q[0] + c[0], y = e.q[1] + c[1] + 4.5 * k;
          var bx = c[2] === 'start' ? x : c[2] === 'end' ? x - tw : x - tw / 2;
          var b = { x: bx - 2 * k, y: y - lb.height * .8, w: tw + 4 * k, h: th + 2 * k };
          var inside = b.x >= view[0] && b.x + b.w <= view[0] + view[2] && b.y >= view[1] && b.y + b.h <= view[1] + view[3];
          if (!fb) fb = [x, y, c[2], b];
          if (inside && !hit(b)) { chosen = [x, y, c[2], b]; break; }
        }
        chosen = chosen || fb;
        e.lbl.setAttribute('x', chosen[0]); e.lbl.setAttribute('y', chosen[1]); e.lbl.setAttribute('text-anchor', chosen[2]);
        if (e.sub) { e.sub.setAttribute('x', chosen[0]); e.sub.setAttribute('y', chosen[1] + 12.5 * k); e.sub.setAttribute('text-anchor', chosen[2]); }
        boxes.push(chosen[3]);
      });
      // Hide region and water names that collide with places in this view.
      Array.prototype.forEach.call(gLabels.querySelectorAll('text'), function (t) {
        t.style.display = '';
        var b = t.getBBox(), m = t.getCTM && t.transform.baseVal.numberOfItems ? t.transform.baseVal.getItem(0).matrix : null, pts = [[b.x, b.y], [b.x + b.width, b.y], [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]];
        if (m) pts = pts.map(function (p) { return [m.a * p[0] + m.c * p[1] + m.e, m.b * p[0] + m.d * p[1] + m.f]; });
        var xs = pts.map(function (p) { return p[0]; }), ys = pts.map(function (p) { return p[1]; });
        var bx = Math.min.apply(null, xs), by = Math.min.apply(null, ys), bw = Math.max.apply(null, xs) - bx, bh = Math.max.apply(null, ys) - by;
        // Rotated labels: test the text's center line in a few steps instead of its full box.
        var hitAny = false;
        for (var s = 0; s <= 6 && !hitAny; s++) {
          var f = s / 6, cx = m ? m.a * (b.x + b.width * f) + m.c * (b.y + b.height / 2) + m.e : b.x + b.width * f, cy = m ? m.b * (b.x + b.width * f) + m.d * (b.y + b.height / 2) + m.f : b.y + b.height / 2;
          var r = b.height / 2;
          if (hit({ x: cx - r, y: cy - r, w: 2 * r, h: 2 * r })) hitAny = true;
        }
        if (!m && hit({ x: bx, y: by, w: bw, h: bh })) hitAny = true;
        if (hitAny) t.style.display = 'none';
      });
      placeCountries(k, boxes, hit);
    }

    // Put each country name at the most central visible point of that country that clears
    // places, other labels, the north arrow and the scale bar. Hidden when nothing fits.
    var SLIDE = [0, 4, -4, 8, -8, 12, -12];
    function placeCountries(k, boxes, hit) {
      if (!cEls.length || gCountries.classList.contains('bm-hidden')) return;
      Array.prototype.forEach.call(gLabels.querySelectorAll('text'), function (t) {
        if (t.style.display === 'none' || t.getAttribute('transform')) return;
        var b = t.getBBox(); boxes.push({ x: b.x, y: b.y, w: b.width, h: b.height });
      });
      [na, sb].forEach(function (g) { var b = g.getBBox(); if (b.width) boxes.push({ x: b.x, y: b.y, w: b.width, h: b.height }); });
      var vx = view[0], vy = view[1], vw = view[2], vh = view[3], areas = [];
      Array.prototype.forEach.call(svg.querySelectorAll('.bm-area'), function (a) {
        if (a.closest('.bm-hidden')) return;
        var b = a.getBBox(); areas.push({ x: b.x, y: b.y, w: b.width, h: b.height });
      });
      function overlaps(list, b) {
        for (var i = 0; i < list.length; i++) { var o = list[i]; if (b.x < o.x + o.w && b.x + b.w > o.x && b.y < o.y + o.h && b.y + b.h > o.y) return true; }
        return false;
      }
      cEls.forEach(function (ce) {
        var t = ce.t;
        t.style.display = '';
        t.setAttribute('x', 0); t.setAttribute('y', 0);
        t.removeAttribute('transform');
        var pad = 3 * k;
        // Horizontal first. In a narrow strip (like the edge of a zoomed-in map) run it vertically,
        // then vertically a little smaller, before giving up.
        var tries = [[0, 1], [1, 1], [1, 0.82]];
        for (var o2 = 0; o2 < tries.length; o2++) {
          var o = tries[o2][0];
          t.style.fontSize = 'calc(' + (ce.size * tries[o2][1]) + 'px*var(--k))';
          var bb0 = t.getBBox(), w = bb0.width, th = bb0.height;
          pad = (o ? 1.5 : 3) * k;
          var bw = o ? th : w, bh = o ? w : th;
          // Candidates slide up to half their border distance to fit inside the view.
          var cands = ce.pts.map(function (p) {
            var x = Math.min(Math.max(p[0], vx + bw / 2 + pad), vx + vw - bw / 2 - pad);
            var y = Math.min(Math.max(p[1], vy + bh / 2 + pad), vy + vh - bh / 2 - pad);
            var moved = Math.max(Math.abs(x - p[0]), Math.abs(y - p[1]));
            return [x, y, p[2] - moved, moved <= p[2] * 0.5];
          }).filter(function (p) { return p[3] && p[2] >= th * 0.6 && vw >= bw + 2 * pad && vh >= bh + 2 * pad; }).map(function (p) {
            var edge = Math.min(p[0] - vx, vx + vw - p[0], p[1] - vy, vy + vh - p[1]);
            return [p, Math.min(p[2], edge)];
          }).sort(function (a, b) { return b[1] - a[1]; });
          // First try to stay clear of shaded "approximate area" ellipses too; if nothing fits, allow them.
          for (var pass = 0; pass < 2; pass++) {
            for (var i = 0; i < cands.length; i++) {
              // Also try sliding a little along the name's length to clear a neighbouring label.
              var p = null, b = null, c0 = cands[i][0];
              for (var j = 0; j < SLIDE.length && !p; j++) {
                var dx = o ? 0 : SLIDE[j] * k, dy = o ? SLIDE[j] * k : 0;
                if (Math.max(Math.abs(dx), Math.abs(dy)) > c0[2] * 0.5) continue;
                var q = [c0[0] + dx, c0[1] + dy], bq = { x: q[0] - bw / 2 - pad, y: q[1] - bh / 2 - pad, w: bw + 2 * pad, h: bh + 2 * pad };
                if (bq.x < vx || bq.y < vy || bq.x + bq.w > vx + vw || bq.y + bq.h > vy + vh) continue;
                if (hit(bq) || (pass === 0 && overlaps(areas, bq))) continue;
                p = q; b = bq;
              }
              if (!p) continue;
              var x = o ? p[0] + th * 0.32 : p[0], y = o ? p[1] : p[1] + th * 0.32;
              t.setAttribute('x', x.toFixed(1)); t.setAttribute('y', y.toFixed(1));
              if (o) t.setAttribute('transform', 'rotate(-90 ' + x.toFixed(1) + ' ' + y.toFixed(1) + ')');
              boxes.push(b);
              return;
            }
          }
        }
        t.style.fontSize = '';
        t.style.display = 'none';
      });
    }

    /* ---------- panel ---------- */
    var cur = 0, CH = C.chapters;
    CH.forEach(function (c, i) {
      var b = h('button', 'bm-tab', '<b>' + (i + 1) + '</b>' + esc(c.tab)); b.type = 'button'; b.setAttribute('role', 'tab');
      b.addEventListener('click', function () { go(i); }); tabs.appendChild(b);
    });
    tabs.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); go(cur + (e.key === 'ArrowRight' ? 1 : -1), true); }
    });
    nav.querySelectorAll('[data-go]').forEach(function (b) { b.addEventListener('click', function () { go(cur + (+b.getAttribute('data-go'))); }); });

    function select(k) {
      var p = PL[k];
      order.forEach(function (n) { plEls[n].g.classList.toggle('sel', n === k); });
      var stats = [];
      if (p.elev != null && !p.area) stats.push('Elevation ≈ ' + fmt(Math.abs(p.elev) * 3.28084) + ' ft (' + fmt(Math.abs(p.elev)) + ' m) ' + (p.elev < 0 ? 'below' : 'above') + ' sea level');
      if (C.anchor && k !== C.anchor && PL[C.anchor]) stats.push('≈ ' + fmt(miles(p.ll, PL[C.anchor].ll)) + ' mi (' + fmt(miles(p.ll, PL[C.anchor].ll) * 1.609) + ' km) from ' + PL[C.anchor].name + ' in a straight line');
      (p.stats || []).forEach(function (s) { stats.push(s); });
      card.innerHTML = '<div class="bm-card-h"><span class="bm-card-t">' + esc(p.name) + (p.sub ? ' <span>· ' + esc(p.sub) + '</span>' : '') + '</span>' +
        '<span class="bm-conf bm-c-' + (p.conf === 'unknown' || p.conf === 'region' ? 'debated' : p.conf) + '">' + esc(p.confT || CONF[p.conf] || '') + '</span></div>' +
        '<p>' + p.text + '</p>' + (stats.length ? '<div class="bm-stats">' + stats.map(function (s) { return '<span>' + esc(s) + '</span>'; }).join('') + '</div>' : '');
    }

    function go(i, focusTab) {
      if (i < 0 || i >= CH.length) return;
      cur = i; var c = CH[i];
      Array.prototype.forEach.call(tabs.children, function (b, j) { b.setAttribute('aria-selected', j === i); b.tabIndex = j === i ? 0 : -1; });
      var tb = tabs.children[i]; if (focusTab) tb.focus();
      if (tabs.scrollWidth > tabs.clientWidth) tabs.scrollLeft = tb.offsetLeft - tabs.clientWidth / 2 + tb.offsetWidth / 2;
      live.innerHTML = '<div class="bm-step">Chapter ' + (i + 1) + ' of ' + CH.length + '</div><div class="bm-ch">' + esc(c.title) + '</div>' +
        '<div class="bm-meta">' + (c.badge ? '<span class="bm-badge" style="background:var(--ink);color:#fff">' + esc(c.badge) + '</span>' : '') +
        (c.refs || []).map(function (r) { return '<span class="bm-badge">' + esc(r[0]) + '</span>'; }).join('') + '</div>' +
        '<div class="bm-text">' + c.html + (c.quote ? '<div class="bm-quote">“' + esc(c.quote[0]) + '”<small>' + esc(c.quote[1]) + '</small></div>' : '') +
        (c.facts && c.facts.length ? '<div class="bm-facts"><b>Did you know?</b><ul>' + c.facts.map(function (f) { return '<li>' + f + '</li>'; }).join('') + '</ul></div>' : '') + '</div>';
      refs.innerHTML = (c.refs && c.refs.length) ? 'Read it: ' + c.refs.map(function (r) { return '<a href="' + bg(r[1] || r[0]) + '" target="_blank" rel="noopener">' + esc(r[0]) + '</a>'; }).join(' · ') : '';
      order.forEach(function (k) {
        var hot = (c.hot || []).indexOf(k) >= 0;
        plEls[k].g.classList.toggle('hot', hot);
        plEls[k].g.classList.toggle('dim', !hot && PL[k].kind !== 'ref' && (c.hot || []).length > 0);
      });
      Object.keys(routeEls).forEach(function (k) {
        var e = routeEls[k], on = (c.routes || []).indexOf(k) >= 0, R = C.routes[k];
        e.classList.remove('draw');
        if (on && R.style !== 'dash') {
          var L = e.getTotalLength(); e.style.setProperty('--len', L); e.style.strokeDasharray = L; e.style.strokeDashoffset = L;
          void e.getBoundingClientRect(); e.classList.add('draw');
        } else if (R.style !== 'dash') { e.style.strokeDasharray = ''; e.style.strokeDashoffset = ''; }
        e.classList.toggle('on', on);
      });
      nav.children[0].disabled = i === 0; nav.children[1].disabled = i === CH.length - 1;
      select(c.sel || (c.hot || [])[0] || order[0]);
      animateTo(viewFor(c));
      layoutLabels();
    }

    var ro = window.ResizeObserver ? new ResizeObserver(function () { scale(); layoutLabels(); }) : null;
    if (ro) ro.observe(svg); else window.addEventListener('resize', function () { scale(); layoutLabels(); });
    setView(viewFor(CH[0]));
    go(0);
  };
})();
