/* Characters Worth Following five-part component: behaviour.
   Built into the snippet by site/story_strip.py as a base64 data: URI (the site's content
   filters mangle inline scripts). Runs right after the top bar, so the bar can move up
   under the post title before the page paints. */
(function () {
  var bar = document.querySelector('.cwf-bar');
  if (!bar || window.cwfReady) return;
  window.cwfReady = true;

  // Move the bar from the top of the post text to just under the title, above the featured image.
  var art = bar.closest('article');
  var head = art && art.querySelector('.page-header');
  if (head && !head.contains(bar)) head.insertAdjacentElement('afterend', bar);

  var NAME = bar.getAttribute('data-name') || '';
  var IMG = bar.getAttribute('data-img') || '';
  var ICON_X = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  var ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>';
  var ICON_PAUSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/></svg>';
  var ICON_BACK = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M9 7.5A11 11 0 1 1 5.2 16"/><path d="M9 3v5h5"/></svg>';
  var ICON_FWD = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M23 7.5A11 11 0 1 0 26.8 16"/><path d="M23 3v5h-5"/></svg>';

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function fmt(t) {
    if (!isFinite(t) || t < 0) t = 0;
    t = Math.floor(t);
    var h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
    return (h ? h + ':' + (m < 10 ? '0' : '') : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  /* ---------- ? panel and Coming soon taps ---------- */
  function closeHelp() {
    var q = bar.querySelector('.cwf-q'), h = bar.querySelector('.cwf-help');
    if (h && !h.hidden) { h.hidden = true; q.setAttribute('aria-expanded', 'false'); }
  }
  function closeSoon(except) {
    var open = document.querySelectorAll('.cwf-step.show');
    for (var i = 0; i < open.length; i++) if (open[i] !== except) open[i].classList.remove('show');
  }

  /* ---------- popup ---------- */
  var modal, audio, lastFocus;

  function steps() { return Array.prototype.slice.call(bar.querySelectorAll('.cwf-step')); }

  function nextAfter(kind) {
    // The next part after this one that is out now.
    var all = steps(), i, idx = -1;
    for (i = 0; i < all.length; i++) if (all[i].getAttribute('data-part') === kind) idx = i;
    for (i = idx + 1; i < all.length; i++) {
      if (!all[i].classList.contains('is-soon') && all[i].tagName === 'A') return all[i];
    }
    return null;
  }

  function build() {
    modal = document.createElement('div');
    modal.className = 'cwf cwf-modal';
    modal.hidden = true;
    modal.innerHTML = '<div class="cwf-m" role="dialog" aria-modal="true" aria-labelledby="cwf-m-t">' +
      '<button type="button" class="cwf-m-x" aria-label="Close">' + ICON_X + '</button>' +
      '<p class="cwf-k"></p><h2 class="cwf-m-t" id="cwf-m-t"></h2><p class="cwf-m-s"></p>' +
      '<div class="cwf-m-media"></div><div class="cwf-m-foot"></div></div>';
    document.body.appendChild(modal);
    modal.addEventListener('click', function (e) {
      if (e.target === modal || e.target.closest('.cwf-m-x')) close();
    });
    modal.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); close(); return; }
      if (e.key !== 'Tab') return;
      var f = modal.querySelectorAll('button,a[href],iframe,input');
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  function stop() {
    if (audio) { audio.pause(); audio.removeAttribute('src'); audio.load(); audio = null; }
    if (modal) modal.querySelector('.cwf-m-media').innerHTML = '';
  }

  function close() {
    if (!modal || modal.hidden) return;
    stop();
    modal.hidden = true;
    document.documentElement.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function open(el) {
    if (!modal) build();
    stop();
    if (modal.hidden) lastFocus = document.activeElement;
    var kind = el.getAttribute('data-cwf-play');
    var title = el.getAttribute('data-cwf-title') || '';
    var num = el.getAttribute('data-cwf-num') || '';
    var href = el.getAttribute('href');
    var song = kind === 'song';
    modal.querySelector('.cwf-k').textContent = 'Characters Worth Following · Part ' + num + ' of 5';
    modal.querySelector('.cwf-m-t').textContent = title;
    modal.querySelector('.cwf-m-s').textContent = NAME + (song ? ' · Gospel Quartet' : ' · Podcast');
    var media = modal.querySelector('.cwf-m-media');
    if (song) {
      var id = el.getAttribute('data-cwf-yt');
      media.innerHTML = '<div class="cwf-m-video"><iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) +
        '?autoplay=1&rel=0&playsinline=1&modestbranding=1" title="' + esc(title) + '" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>';
    } else {
      player(media, el.getAttribute('data-cwf-audio'), +el.getAttribute('data-cwf-min') || 0, href);
    }
    var nxt = nextAfter(kind), foot = '';
    foot += '<a class="cwf-m-out" href="' + esc(href) + '" target="_blank" rel="noopener">' + (song ? 'Watch on YouTube' : 'Open on Substack') + ' ↗</a>';
    if (nxt) {
      var lbl = nxt.getAttribute('data-label');
      foot += nxt.hasAttribute('data-cwf-play')
        ? '<button type="button" class="cwf-m-next" data-next="' + esc(nxt.getAttribute('data-part')) + '">Next: ' + esc(lbl) + ' →</button>'
        : '<a class="cwf-m-next" href="' + esc(nxt.getAttribute('href')) + '">Next: ' + esc(lbl) + ' →</a>';
    }
    modal.querySelector('.cwf-m-foot').innerHTML = foot;
    var nb = modal.querySelector('button.cwf-m-next');
    if (nb) nb.addEventListener('click', function () {
      open(bar.querySelector('.cwf-step[data-part="' + nb.getAttribute('data-next') + '"]'));
    });
    modal.hidden = false;
    document.documentElement.style.overflow = 'hidden';
    var focusTarget = song ? modal.querySelector('.cwf-m-x') : modal.querySelector('.cwf-pl-play');
    (focusTarget || modal.querySelector('.cwf-m-x')).focus();
  }

  function player(media, src, minutes, href) {
    media.innerHTML = '<div class="cwf-pl is-loading">' +
      (IMG ? '<img class="cwf-pl-img" src="' + esc(IMG) + '" alt="">' : '') +
      '<div class="cwf-pl-main"><div class="cwf-pl-row">' +
      '<button type="button" class="cwf-pl-skip" data-skip="-15" aria-label="Back 15 seconds">' + ICON_BACK + '<span>15</span></button>' +
      '<button type="button" class="cwf-pl-play" aria-label="Play">' + ICON_PLAY + '</button>' +
      '<button type="button" class="cwf-pl-skip" data-skip="30" aria-label="Forward 30 seconds">' + ICON_FWD + '<span>30</span></button>' +
      '<button type="button" class="cwf-pl-rate" aria-label="Playback speed">1×</button></div>' +
      '<input type="range" class="cwf-pl-seek" min="0" max="1000" value="0" step="1" aria-label="Position in episode">' +
      '<div class="cwf-pl-time"><span class="cwf-pl-cur">0:00</span><span class="cwf-pl-left">-' + fmt(minutes * 60) + '</span></div>' +
      '<p class="cwf-pl-err" hidden>The episode didn’t load here. <a href="' + esc(href) + '" target="_blank" rel="noopener" style="color:#fff;text-decoration:underline">Listen on Substack ↗</a></p>' +
      '</div></div>';
    var box = media.querySelector('.cwf-pl'), play = box.querySelector('.cwf-pl-play'), seek = box.querySelector('.cwf-pl-seek');
    var cur = box.querySelector('.cwf-pl-cur'), left = box.querySelector('.cwf-pl-left'), rate = box.querySelector('.cwf-pl-rate');
    var a = audio = new Audio();
    a.preload = 'auto';
    a.src = src;
    var dragging = false, rates = [1, 1.25, 1.5, 2];
    function dur() { return isFinite(a.duration) && a.duration > 0 ? a.duration : minutes * 60; }
    function paint() {
      var d = dur(), p = d ? a.currentTime / d : 0;
      if (!dragging) seek.value = Math.round(p * 1000);
      seek.style.setProperty('--p', (seek.value / 10) + '%');
      cur.textContent = fmt(dragging ? seek.value / 1000 * d : a.currentTime);
      left.textContent = '-' + fmt(d - (dragging ? seek.value / 1000 * d : a.currentTime));
    }
    function state() {
      var on = !a.paused;
      play.innerHTML = on ? ICON_PAUSE : ICON_PLAY;
      play.setAttribute('aria-label', on ? 'Pause' : 'Play');
    }
    a.addEventListener('timeupdate', paint);
    a.addEventListener('loadedmetadata', paint);
    a.addEventListener('play', state);
    a.addEventListener('pause', state);
    a.addEventListener('ended', state);
    a.addEventListener('waiting', function () { box.classList.add('is-loading'); });
    a.addEventListener('playing', function () { box.classList.remove('is-loading'); });
    a.addEventListener('canplay', function () { box.classList.remove('is-loading'); });
    a.addEventListener('error', function () {
      if (audio !== a) return;
      box.classList.remove('is-loading');
      box.querySelector('.cwf-pl-err').hidden = false;
    });
    play.addEventListener('click', function () {
      if (a.paused) { var pr = a.play(); if (pr && pr.catch) pr.catch(function () {}); } else a.pause();
    });
    box.addEventListener('click', function (e) {
      var s = e.target.closest('[data-skip]');
      if (!s) return;
      a.currentTime = Math.max(0, Math.min(dur(), a.currentTime + (+s.getAttribute('data-skip'))));
      paint();
    });
    rate.addEventListener('click', function () {
      var i = (rates.indexOf(a.playbackRate) + 1) % rates.length;
      a.playbackRate = rates[i];
      rate.textContent = rates[i] + '×';
    });
    seek.addEventListener('input', function () { dragging = true; paint(); });
    seek.addEventListener('change', function () {
      a.currentTime = seek.value / 1000 * dur();
      dragging = false;
      paint();
    });
    var pr = a.play();  // the click that opened the popup lets playback start
    if (pr && pr.catch) pr.catch(function () { state(); });
    paint();
  }

  /* ---------- clicks ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target;
    var q = t.closest('.cwf-q');
    if (q) {
      var h = q.parentNode.querySelector('.cwf-help');
      var on = h.hidden;
      h.hidden = !on;
      q.setAttribute('aria-expanded', on ? 'true' : 'false');
      return;
    }
    if (!t.closest('.cwf-help')) closeHelp();
    var soon = t.closest('.cwf-step.is-soon');
    closeSoon(soon);
    if (soon) { soon.classList.toggle('show'); return; }
    var p = t.closest('[data-cwf-play]');
    if (p && !(e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button)) {
      e.preventDefault();
      open(p);
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeHelp(); closeSoon(null); }
  });
})();
