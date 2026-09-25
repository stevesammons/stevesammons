/* Play YouTube links in a lightbox instead of sending readers to YouTube.
   Any link to a single video (watch?v=, youtu.be/, shorts/, embed/) opens an on-page player;
   channel and playlist links are left alone. Ctrl/Cmd/Shift-click and middle-click still
   open YouTube, and without JavaScript the plain link keeps working. */
(function () {
  if (document.documentElement.dataset.ssVideo) return;
  document.documentElement.dataset.ssVideo = '1';
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }

  function videoOf(href) {
    var u;
    try { u = new URL(href, location.href); } catch (e) { return null; }
    var host = u.hostname.replace(/^(www|m|music)\./, ''), id = null;
    if (host === 'youtu.be') id = u.pathname.slice(1).split('/')[0];
    else if (host === 'youtube.com' || host === 'youtube-nocookie.com') {
      if (u.pathname === '/watch') id = u.searchParams.get('v');
      else {
        var m = u.pathname.match(/^\/(shorts|embed|live)\/([^/?#]+)/);
        if (m) id = m[2];
      }
    }
    if (!id || !/^[\w-]{11}$/.test(id)) return null;
    var t = u.searchParams.get('t') || u.searchParams.get('start') || '', start = 0;
    if (/^\d+s?$/.test(t)) start = parseInt(t, 10);
    else if (t) {
      var h = t.match(/(\d+)h/), mi = t.match(/(\d+)m/), s = t.match(/(\d+)s/);
      start = (h ? +h[1] * 3600 : 0) + (mi ? +mi[1] * 60 : 0) + (s ? +s[1] : 0);
    }
    return { id: id, start: start, vertical: /^\/shorts\//.test(u.pathname) };
  }

  function init() {
    var css = [
      'a.ss-vid-short{white-space:nowrap}',
      'a.ss-vid-text{overflow-wrap:anywhere}',
      'a.ss-vid-text::after{content:"";display:inline-block;width:.95em;height:.95em;margin-left:.3em;vertical-align:-.12em;border-radius:50%;background:#dd3333 url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3E%3Cpath d=%27M6 4.5v7l5.5-3.5z%27 fill=%27%23fff%27/%3E%3C/svg%3E") center/100% no-repeat;transition:transform .15s}',
      'a.ss-vid-text:hover::after,a.ss-vid-text:focus-visible::after{transform:scale(1.18)}',
      'a.ss-vid-card{display:block;position:relative;cursor:pointer}',
      'a.ss-vid-card img{transition:transform .2s,box-shadow .2s}',
      'a.ss-vid-card:hover img,a.ss-vid-card:focus-visible img{transform:translateY(-2px);box-shadow:0 8px 22px rgba(0,0,0,.14)}',
      '.ss-vid{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:max(16px,env(safe-area-inset-top)) 16px 16px;background:rgba(10,10,10,.88);opacity:0;transition:opacity .2s}',
      '.ss-vid.is-open{opacity:1}',
      '.ss-vid-box{position:relative;width:min(960px,100%,calc((100vh - 120px) * 16 / 9));transform:scale(.97);transition:transform .2s}',
      '.ss-vid.is-open .ss-vid-box{transform:none}',
      '.ss-vid-box.is-vertical{width:min(420px,100%,calc((100vh - 120px) * 9 / 16))}',
      '.ss-vid-frame{position:relative;aspect-ratio:16/9;background:#000;border-radius:6px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.5)}',
      '.ss-vid-box.is-vertical .ss-vid-frame{aspect-ratio:9/16}',
      '.ss-vid-frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0}',
      '.ss-vid-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;color:#fff;font-size:15px;line-height:1.3}',
      '.ss-vid-title{font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;border-left:3px solid #dd3333;padding-left:10px}',
      '.ss-vid-close{flex:0 0 auto;display:grid;place-items:center;width:40px;height:40px;border:0;border-radius:50%;background:#dd3333;color:#fff;font-size:26px;line-height:1;cursor:pointer;padding:0;transition:transform .15s}',
      '.ss-vid-close:hover{transform:scale(1.08)}',
      '.ss-vid-close:focus-visible{outline:2px solid #fff;outline-offset:3px}',
      '.ss-vid-yt{display:inline-block;margin-top:10px;color:#ccc;font-size:13px;text-decoration:underline;text-underline-offset:3px}',
      '.ss-vid-yt:hover{color:#fff}',
      'html.ss-vid-lock,html.ss-vid-lock body{overflow:hidden}',
      '@media (prefers-reduced-motion:reduce){.ss-vid,.ss-vid-box,a.ss-vid-card img{transition:none}}'
    ].join('');
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    // Mark links so readers can see they play here.
    var links = document.querySelectorAll('a[href*="youtu"]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      if (!videoOf(a.href) || a.closest('header,footer,nav,.ss-vid')) continue;
      var card = !!a.querySelector('img');
      a.classList.add(card ? 'ss-vid-card' : 'ss-vid-text');
      if (!card && a.textContent.trim().length <= 24) a.classList.add('ss-vid-short'); // keep icon with the word
      a.setAttribute('aria-haspopup', 'dialog');
      if (!a.getAttribute('title')) a.setAttribute('title', isPronunciation(a) ? 'Hear it pronounced' : 'Play video');
    }

    document.addEventListener('click', function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest && e.target.closest('a.ss-vid-text, a.ss-vid-card');
      if (!a) return;
      var v = videoOf(a.href);
      if (!v) return;
      e.preventDefault();
      open(v, a);
    });
  }

  function isPronunciation(a) {
    var prev = a.previousSibling;
    return !a.querySelector('img') && !!prev && prev.nodeType === 3 && /\(\s*$/.test(prev.textContent);
  }

  function labelFor(a) {
    var img = a.querySelector('img');
    if (img && img.alt) return img.alt;
    var text = a.textContent.trim();
    if (!text || /^https?:\/\//.test(text)) return 'Video';
    // Pronunciation links sit in "Name (<a>NAME-say</a>)": show "Name, pronounced ...".
    var prev = a.previousSibling, name = '';
    if (prev && prev.nodeType === 3 && /\(\s*$/.test(prev.textContent)) {
      var before = prev.textContent.replace(/\(\s*$/, '').trim(), p = prev.previousSibling;
      name = (before || (p && p.textContent) || '').trim().split(/\s+/).pop();
    }
    return name ? name + ' · pronounced “' + text + '”' : text;
  }

  function open(v, trigger) {
    // No autoplay=1: some browsers answer it with "Video unavailable". Load the normal player
    // and ask it to play through the iframe API; if that is refused, the play button is still there.
    var src = 'https://www.youtube.com/embed/' + v.id + '?rel=0&playsinline=1&enablejsapi=1&origin=' +
      encodeURIComponent(location.origin) + (v.start ? '&start=' + v.start : '');
    var watch = 'https://www.youtube.com/watch?v=' + v.id + (v.start ? '&t=' + v.start + 's' : '');

    var wrap = document.createElement('div');
    wrap.className = 'ss-vid';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.setAttribute('aria-label', labelFor(trigger));
    wrap.innerHTML =
      '<div class="ss-vid-box' + (v.vertical ? ' is-vertical' : '') + '">' +
        '<div class="ss-vid-bar"><span class="ss-vid-title"></span>' +
        '<button type="button" class="ss-vid-close" aria-label="Close video">&times;</button></div>' +
        '<div class="ss-vid-frame"><iframe allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen ' +
        'referrerpolicy="strict-origin-when-cross-origin"></iframe></div>' +
        '<a class="ss-vid-yt" target="_blank" rel="noopener">Watch on YouTube</a>' +
      '</div>';
    wrap.querySelector('.ss-vid-title').textContent = labelFor(trigger);
    wrap.querySelector('iframe').title = labelFor(trigger);
    var frame = wrap.querySelector('iframe');
    frame.addEventListener('load', function () {
      [200, 700, 1500].forEach(function (ms) {
        setTimeout(function () {
          if (!frame.contentWindow || frame.src === 'about:blank') return;
          frame.contentWindow.postMessage('{"event":"listening","id":1}', '*');
          frame.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
        }, ms);
      });
    }, { once: true });
    frame.src = src;
    wrap.querySelector('.ss-vid-yt').href = watch;
    document.body.appendChild(wrap);
    document.documentElement.classList.add('ss-vid-lock');
    requestAnimationFrame(function () { wrap.classList.add('is-open'); });

    var closeBtn = wrap.querySelector('.ss-vid-close');
    closeBtn.focus({ preventScroll: true });

    function close() {
      document.removeEventListener('keydown', onKey, true);
      wrap.querySelector('iframe').src = 'about:blank'; // stop playback right away
      wrap.classList.remove('is-open');
      document.documentElement.classList.remove('ss-vid-lock');
      setTimeout(function () { wrap.remove(); }, 200);
      if (trigger && trigger.focus) trigger.focus({ preventScroll: true });
    }
    function onKey(e) {
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      else if (e.key === 'Tab') { // keep focus inside the dialog
        var f = [closeBtn, wrap.querySelector('iframe'), wrap.querySelector('.ss-vid-yt')];
        var i = f.indexOf(document.activeElement);
        if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
      }
    }
    closeBtn.addEventListener('click', close);
    wrap.addEventListener('click', function (e) { if (e.target === wrap) close(); });
    document.addEventListener('keydown', onKey, true);
  }
})();
