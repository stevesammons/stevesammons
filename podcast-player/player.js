/* Play Substack podcast episodes on the page.
   apply.py prepends window.SS_POD_EPS = {slug: {src, title, dur, img, url}} for the episodes the
   post links to. Clicking a "Listen to the podcast" card (a link to sammons.substack.com/p/<slug>)
   turns it into a player; a mini bar keeps the controls on screen while the reader scrolls.
   Links to episodes that aren't in SS_POD_EPS (not out on Substack yet) are left alone. */
(function () {
  if (document.documentElement.dataset.ssPod) return;
  document.documentElement.dataset.ssPod = '1';
  var EPS = window.SS_POD_EPS || {};

  var RED = '#dd3333';
  var PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg>';
  var PAUSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" fill="currentColor"/></svg>';
  function skipIcon(fwd) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' +
      (fwd ? 'M12 5V2l5 4-5 4V7a6 6 0 1 0 6 6h2a8 8 0 1 1-8-8z' : 'M12 5V2L7 6l5 4V7a6 6 0 1 1-6 6H4a8 8 0 1 0 8-8z') +
      '" fill="currentColor"/><text x="12" y="16" text-anchor="middle" font-size="7" font-weight="700" fill="currentColor" font-family="sans-serif">15</text></svg>';
  }
  var SPEEDS = [1, 1.25, 1.5, 1.75, 2, 0.75];

  function slugOf(href) {
    try {
      var u = new URL(href, location.href);
      if (!/(^|\.)substack\.com$/.test(u.hostname)) return null;
      var m = u.pathname.match(/^\/p\/([^/]+)/);
      return m && EPS[m[1]] ? m[1] : null;
    } catch (e) { return null; }
  }
  function fmt(s) {
    s = Math.max(0, Math.floor(s || 0));
    var h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
    return (h ? h + ':' + (m < 10 ? '0' : '') : '') + m + ':' + (x < 10 ? '0' : '') + x;
  }
  function store(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} }
  function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

  function init() {
    var cards = [];
    document.querySelectorAll('a[href*="substack.com/p/"]').forEach(function (a) {
      var slug = slugOf(a.href);
      if (!slug || a.closest('header,footer,nav,.ss-pod')) return;
      a.setAttribute('aria-label', 'Play the podcast here: ' + EPS[slug].title);
      a.setAttribute('title', 'Play the podcast');
      a.classList.add(a.querySelector('img') ? 'ss-pod-card' : 'ss-pod-link');
      cards.push(a);
    });
    if (!cards.length) return;

    var css = [
      'a.ss-pod-card{display:block;position:relative;cursor:pointer}',
      'a.ss-pod-card img{transition:transform .2s,box-shadow .2s}',
      'a.ss-pod-card:hover img,a.ss-pod-card:focus-visible img{transform:translateY(-2px);box-shadow:0 8px 22px rgba(0,0,0,.14)}',
      '.ss-pod{--r:' + RED + ';display:grid;grid-template-columns:112px 1fr;gap:4px 18px;align-items:center;margin:0;padding:18px;border:3px solid #1a1a1a;border-radius:18px;background:#f5f5f3;color:#1a1a1a;font-size:15px;line-height:1.35;text-align:left}',
      '.ss-pod-art{grid-row:span 2;width:112px;height:112px;border-radius:10px;object-fit:cover;background:#ddd;display:block}',
      '.ss-pod-kicker{display:block;color:var(--r);font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}',
      '.ss-pod-main{align-self:end}','.ss-pod-controls{align-self:start;min-width:0}','.ss-pod-title{display:block;font-weight:700;font-size:1.12em;margin:2px 0 6px}',
      '.ss-pod-row{display:flex;align-items:center;gap:10px}',
      '.ss-pod button{display:grid;place-items:center;border:0;padding:0;margin:0;cursor:pointer;background:none;color:#1a1a1a;font:inherit;line-height:1}',
      '.ss-pod button:focus-visible,.ss-pod-bar button:focus-visible{outline:2px solid var(--r);outline-offset:2px;border-radius:50%}',
      '.ss-pod button svg{width:26px;height:26px}',
      '.ss-pod .ss-pod-play{flex:0 0 auto;width:48px;height:48px;border-radius:50%;background:var(--r);color:#fff;transition:transform .15s}',
      '.ss-pod .ss-pod-play:hover{transform:scale(1.06)}',
      '.ss-pod .ss-pod-play svg{width:24px;height:24px}',
      '.ss-pod-seek{flex:1 1 auto;min-width:60px;height:24px;margin:0;accent-color:var(--r);cursor:pointer;background:transparent}',
      '.ss-pod-time{flex:0 0 auto;font-variant-numeric:tabular-nums;font-size:13px;color:#555;white-space:nowrap}',
      '.ss-pod .ss-pod-speed{flex:0 0 auto;min-width:44px;height:28px;padding:0 8px;border:2px solid #1a1a1a;border-radius:14px;font-size:13px;font-weight:700}',
      '.ss-pod-foot{display:flex;justify-content:space-between;gap:10px;margin-top:8px;font-size:12px;color:#666}',
      '.ss-pod-foot a{color:#666;text-decoration:underline;text-underline-offset:3px}',
      '@media (max-width:560px){.ss-pod{grid-template-columns:64px 1fr;gap:12px;padding:14px}' +
        '.ss-pod-art{grid-row:auto;width:64px;height:64px}.ss-pod-main{align-self:center}.ss-pod-title{margin-bottom:0}' +
        '.ss-pod-controls{grid-column:1/-1}.ss-pod-row{flex-wrap:wrap;row-gap:4px}' +
        '.ss-pod-seek{order:9;flex-basis:100%}.ss-pod-time{margin-left:auto}}',
      '.ss-pod-bar{--r:' + RED + ';position:fixed;left:0;right:0;bottom:0;z-index:2147482000;display:flex;align-items:center;gap:12px;padding:10px max(16px,env(safe-area-inset-right)) calc(10px + env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left));background:#141414;color:#fff;font-size:14px;line-height:1.3;box-shadow:0 -6px 20px rgba(0,0,0,.25);transform:translateY(110%);transition:transform .25s}',
      '.ss-pod-bar.is-on{transform:none}',
      '.ss-pod-bar-line{position:absolute;left:0;top:0;height:3px;background:var(--r);width:0}',
      '.ss-pod-bar button{display:grid;place-items:center;flex:0 0 auto;border:0;padding:0;cursor:pointer;background:none;color:#fff;line-height:1}',
      '.ss-pod-bar .ss-pod-play{width:40px;height:40px;border-radius:50%;background:var(--r)}',
      '.ss-pod-bar .ss-pod-play svg{width:20px;height:20px}',
      '.ss-pod-bar .ss-pod-skip svg{width:24px;height:24px}',
      '.ss-pod-bar-text{flex:1 1 auto;min-width:0;cursor:pointer}',
      '.ss-pod-bar-title{display:block;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
      '.ss-pod-bar-time{display:block;font-size:12px;color:#bbb;font-variant-numeric:tabular-nums}',
      '.ss-pod-bar .ss-pod-close{width:32px;height:32px;font-size:24px;color:#bbb}',
      '@media (max-width:420px){.ss-pod-bar .ss-pod-skip{display:none}}',
      '@media (prefers-reduced-motion:reduce){.ss-pod-bar,a.ss-pod-card img,.ss-pod .ss-pod-play{transition:none}}'
    ].join('');
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    document.addEventListener('click', function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest && e.target.closest('a.ss-pod-card, a.ss-pod-link');
      if (!a) return;
      var slug = slugOf(a.href);
      if (!slug) return;
      e.preventDefault();
      // A text link plays through the card for the same episode when there is one.
      var card = cards.filter(function (c) { return c.classList.contains('ss-pod-card') && slugOf(c.href) === slug; })[0];
      var target = card || a;
      var p = build(slug, target);
      p.el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      p.play();
    });
  }

  var bar, current;

  function build(slug, anchor) {
    var ep = EPS[slug], key = 'ss-pod:' + slug;
    var el = document.createElement('div');
    el.className = 'ss-pod';
    el.setAttribute('role', 'region');
    el.setAttribute('aria-label', 'Podcast player: ' + ep.title);
    el.innerHTML =
      '<img class="ss-pod-art" alt="" loading="lazy">' +
      '<div class="ss-pod-main"><span class="ss-pod-kicker">Companion podcast</span><span class="ss-pod-title"></span></div>' +
      '<div class="ss-pod-controls"><div class="ss-pod-row">' +
        '<button type="button" class="ss-pod-skip" data-skip="-15" aria-label="Back 15 seconds">' + skipIcon(false) + '</button>' +
        '<button type="button" class="ss-pod-play" aria-label="Play">' + PLAY + '</button>' +
        '<button type="button" class="ss-pod-skip" data-skip="15" aria-label="Forward 15 seconds">' + skipIcon(true) + '</button>' +
        '<input class="ss-pod-seek" type="range" min="0" max="1000" value="0" step="1" aria-label="Seek">' +
        '<span class="ss-pod-time">0:00 / ' + fmt(ep.dur) + '</span>' +
        '<button type="button" class="ss-pod-speed" aria-label="Playback speed">1×</button>' +
      '</div><div class="ss-pod-foot"><span class="ss-pod-note"></span>' +
        '<a target="_blank" rel="noopener">Open on Substack</a></div></div>';
    el.querySelector('.ss-pod-title').textContent = ep.title;
    el.querySelector('.ss-pod-art').src = ep.img || '';
    if (!ep.img) el.querySelector('.ss-pod-art').remove();
    el.querySelector('.ss-pod-foot a').href = ep.url;

    var audio = new Audio();
    audio.preload = 'metadata';
    audio.src = ep.src;
    var playBtn = el.querySelector('.ss-pod-play'), seek = el.querySelector('.ss-pod-seek');
    var time = el.querySelector('.ss-pod-time'), note = el.querySelector('.ss-pod-note');
    var speedBtn = el.querySelector('.ss-pod-speed'), seeking = false;
    function dur() { return isFinite(audio.duration) && audio.duration > 0 ? audio.duration : ep.dur || 0; }

    var saved = parseFloat(load(key) || '0');
    if (saved > 5 && saved < (ep.dur || 1e9) - 10) {
      audio.currentTime = saved;
      note.textContent = 'Picking up where you left off, at ' + fmt(saved);
    }
    var rate = parseFloat(load('ss-pod:rate') || '1');
    if (SPEEDS.indexOf(rate) >= 0) { audio.playbackRate = rate; audio.defaultPlaybackRate = rate; }
    speedBtn.textContent = audio.playbackRate + '×';

    var p = {
      el: el, audio: audio, ep: ep,
      play: function () {
        if (current && current !== p) current.audio.pause();
        current = p;
        var r = audio.play();
        if (r && r.catch) r.catch(function () { note.textContent = 'Tap play to start.'; });
      },
      toggle: function () { if (audio.paused) p.play(); else audio.pause(); },
      skip: function (s) { audio.currentTime = Math.min(Math.max(0, audio.currentTime + s), dur()); }
    };

    function sync() {
      var d = dur(), t = audio.currentTime;
      if (!seeking) seek.value = d ? Math.round(t / d * 1000) : 0;
      seek.setAttribute('aria-valuetext', fmt(t) + ' of ' + fmt(d));
      time.textContent = fmt(t) + ' / ' + fmt(d);
      if (bar && current === p) {
        bar.line.style.width = (d ? t / d * 100 : 0) + '%';
        bar.time.textContent = fmt(t) + ' / ' + fmt(d);
      }
    }
    function state() {
      var icon = audio.paused ? PLAY : PAUSE, label = audio.paused ? 'Play' : 'Pause';
      playBtn.innerHTML = icon; playBtn.setAttribute('aria-label', label);
      if (bar && current === p) { bar.play.innerHTML = icon; bar.play.setAttribute('aria-label', label); }
      if ('mediaSession' in navigator) navigator.mediaSession.playbackState = audio.paused ? 'paused' : 'playing';
    }
    var lastSave = 0;
    audio.addEventListener('timeupdate', function () {
      sync();
      if (Math.abs(audio.currentTime - lastSave) >= 5) { lastSave = audio.currentTime; store(key, String(Math.floor(audio.currentTime))); }
    });
    audio.addEventListener('loadedmetadata', sync);
    audio.addEventListener('play', function () { note.textContent = ''; state(); showBar(p); mediaSession(p); });
    audio.addEventListener('pause', function () { state(); store(key, String(Math.floor(audio.currentTime))); });
    audio.addEventListener('ended', function () { store(key, null); state(); });
    audio.addEventListener('waiting', function () { note.textContent = 'Loading…'; });
    audio.addEventListener('playing', function () { note.textContent = ''; });
    audio.addEventListener('error', function () {
      note.innerHTML = 'This episode could not load here. ';
      var a = document.createElement('a'); a.href = ep.url; a.target = '_blank'; a.rel = 'noopener';
      a.textContent = 'Listen on Substack'; note.appendChild(a);
    });

    playBtn.addEventListener('click', p.toggle);
    el.querySelectorAll('.ss-pod-skip').forEach(function (b) {
      b.addEventListener('click', function () { p.skip(parseFloat(b.getAttribute('data-skip'))); });
    });
    seek.addEventListener('input', function () {
      seeking = true;
      time.textContent = fmt(seek.value / 1000 * dur()) + ' / ' + fmt(dur());
    });
    seek.addEventListener('change', function () { audio.currentTime = seek.value / 1000 * dur(); seeking = false; });
    speedBtn.addEventListener('click', function () {
      var r = SPEEDS[(SPEEDS.indexOf(audio.playbackRate) + 1) % SPEEDS.length] || 1;
      audio.playbackRate = audio.defaultPlaybackRate = r;
      speedBtn.textContent = r + '×';
      store('ss-pod:rate', String(r));
    });

    // Swap the card for the player, keeping the surrounding figure.
    anchor.replaceWith(el);
    sync();
    state();
    watch(p);
    return p;
  }

  function mediaSession(p) {
    if (!('mediaSession' in navigator) || !window.MediaMetadata) return;
    try {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: p.ep.title, artist: 'Steve Sammons', album: 'Companion podcast',
        artwork: p.ep.img ? [{ src: p.ep.img, sizes: '512x512' }] : []
      });
      navigator.mediaSession.setActionHandler('play', function () { p.play(); });
      navigator.mediaSession.setActionHandler('pause', function () { p.audio.pause(); });
      navigator.mediaSession.setActionHandler('seekbackward', function () { p.skip(-15); });
      navigator.mediaSession.setActionHandler('seekforward', function () { p.skip(15); });
    } catch (e) {}
  }

  // Mini bar: shown once an episode has started and its player is scrolled out of view.
  var inView = true, dismissed = false;
  function watch(p) {
    if (!('IntersectionObserver' in window)) { inView = false; return; }
    new IntersectionObserver(function (en) {
      if (current && current !== p) return;
      inView = en[0].isIntersecting;
      if (inView) dismissed = false;
      updateBar();
    }).observe(p.el);
  }
  function makeBar() {
    var b = document.createElement('div');
    b.className = 'ss-pod-bar';
    b.setAttribute('role', 'region');
    b.setAttribute('aria-label', 'Podcast mini player');
    b.innerHTML = '<span class="ss-pod-bar-line"></span>' +
      '<button type="button" class="ss-pod-skip" aria-label="Back 15 seconds">' + skipIcon(false) + '</button>' +
      '<button type="button" class="ss-pod-play" aria-label="Pause">' + PAUSE + '</button>' +
      '<button type="button" class="ss-pod-skip" aria-label="Forward 15 seconds">' + skipIcon(true) + '</button>' +
      '<span class="ss-pod-bar-text" title="Back to the player"><span class="ss-pod-bar-title"></span><span class="ss-pod-bar-time"></span></span>' +
      '<button type="button" class="ss-pod-close" aria-label="Stop and close">&times;</button>';
    document.body.appendChild(b);
    var skips = b.querySelectorAll('.ss-pod-skip');
    bar = { el: b, line: b.querySelector('.ss-pod-bar-line'), play: b.querySelector('.ss-pod-play'),
            title: b.querySelector('.ss-pod-bar-title'), time: b.querySelector('.ss-pod-bar-time') };
    skips[0].addEventListener('click', function () { current && current.skip(-15); });
    skips[1].addEventListener('click', function () { current && current.skip(15); });
    bar.play.addEventListener('click', function () { current && current.toggle(); });
    b.querySelector('.ss-pod-bar-text').addEventListener('click', function () {
      current && current.el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    });
    b.querySelector('.ss-pod-close').addEventListener('click', function () {
      if (current) current.audio.pause();
      dismissed = true;
      updateBar();
    });
  }
  function showBar(p) {
    if (!bar) makeBar();
    bar.title.textContent = p.ep.title;
    dismissed = false;
    updateBar();
  }
  function updateBar() {
    if (!bar || !current) return;
    var started = current.audio.currentTime > 0 || !current.audio.paused;
    bar.el.classList.toggle('is-on', started && !inView && !dismissed);
  }

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }
})();
