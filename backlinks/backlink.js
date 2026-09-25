/* "Back to the story" links for reference pages (character profiles and place maps).
   Markup: <div class="ss-back" data-posts="2943,3001"></div> (add ss-back--end for the bottom copy).
   Only published posts are ever linked: titles and URLs come from the public REST API,
   which does not return scheduled posts. */
(function () {
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }
  function init() {
  var slots = document.querySelectorAll('.ss-back[data-posts]');
  if (!slots.length || document.documentElement.dataset.ssBack) return;
  document.documentElement.dataset.ssBack = '1';

  var css = [
    '.ss-back{margin:0 0 28px}',
    '.ss-back--end{margin:36px 0 0}',
    '.ss-back:empty{display:none}',
    '.ss-back a.ss-back-card{display:flex;align-items:center;gap:14px;padding:14px 18px;border-left:4px solid #dd3333;background:#f5f5f3;color:#000;text-decoration:none;border-radius:0 4px 4px 0;transition:background .15s}',
    '.ss-back a.ss-back-card:hover,.ss-back a.ss-back-card:focus-visible{background:#ecebe6;color:#000}',
    '.ss-back a.ss-back-card:focus-visible{outline:2px solid #dd3333;outline-offset:2px}',
    '.ss-back-arrow{flex:0 0 auto;display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:#dd3333;color:#fff;font-size:18px;line-height:1;transition:transform .15s}',
    '.ss-back a.ss-back-card:hover .ss-back-arrow{transform:translateX(-3px)}',
    '.ss-back-kicker{display:block;font-size:.72em;letter-spacing:.12em;text-transform:uppercase;color:#777;font-weight:700}',
    '.ss-back-title{display:block;font-weight:700;line-height:1.35}',
    '.ss-back-list{padding:14px 18px;border-left:4px solid #dd3333;background:#f5f5f3;border-radius:0 4px 4px 0}',
    '.ss-back-list ul{margin:6px 0 0;padding:0;list-style:none}',
    '.ss-back-list li{margin:4px 0}',
    '.ss-back-list li a{color:#000;font-weight:700;text-decoration:underline;text-decoration-color:#dd3333;text-underline-offset:3px}',
    '.ss-back--end a.ss-back-card{padding:10px 16px}',
    '.ss-back--end .ss-back-arrow{width:28px;height:28px;font-size:15px}'
  ].join('');
  var st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);

  var ids = [];
  slots.forEach(function (s) {
    s.getAttribute('data-posts').split(',').forEach(function (v) {
      v = parseInt(v, 10);
      if (v && ids.indexOf(v) < 0) ids.push(v);
    });
  });

  var KEY = 'ss-back-origin';
  function store(o) { try { sessionStorage.setItem(KEY, JSON.stringify(o)); } catch (e) {} }
  function load() { try { return JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) { return null; } }
  function esc(t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
  function norm(u) {
    try { var x = new URL(u, location.href); return x.origin + x.pathname.replace(/\/+$/, ''); } catch (e) { return ''; }
  }
  // Post ID from a same-site URL such as /?p=2943 or /?p=2943&preview=true
  function idFromUrl(u) {
    try {
      var x = new URL(u);
      if (x.origin !== location.origin) return 0;
      return parseInt(x.searchParams.get('p') || x.searchParams.get('preview_id') || '0', 10);
    } catch (e) { return 0; }
  }

  function render(published, origin) {
    slots.forEach(function (s) {
      var end = s.classList.contains('ss-back--end');
      if (origin) {
        var page = origin.kind === 'page';
        var label = origin.title ? origin.title : page ? 'the previous page' : 'the post you were reading';
        s.innerHTML = '<a class="ss-back-card" href="' + esc(origin.url) + '">' +
          '<span class="ss-back-arrow" aria-hidden="true">&larr;</span>' +
          '<span><span class="ss-back-kicker">' + (page ? 'Back to' : 'Back to the story') + '</span>' +
          '<span class="ss-back-title">' + esc(label) + '</span></span></a>';
        s.firstChild.addEventListener('click', function (e) {
          // Return to the same scroll position when the story is the previous page.
          if (document.referrer && norm(document.referrer) === norm(origin.url) && history.length > 1) {
            e.preventDefault();
            history.back();
          }
        });
      } else if (published.length && !end) {
        var subject = s.getAttribute('data-subject');
        s.innerHTML = '<div class="ss-back-list"><span class="ss-back-kicker">' +
          (subject ? esc(subject) + ' appears in' : 'Read the story') + '</span><ul>' +
          published.map(function (p) {
            return '<li><a href="' + esc(p.link) + '">' + esc(p.title) + '</a> &rarr;</li>';
          }).join('') + '</ul></div>';
      } else {
        s.innerHTML = '';
      }
    });
  }

  function decide(published) {
    var ref = document.referrer, refId = idFromUrl(ref), origin = null;
    var match = published.filter(function (p) { return norm(p.link) === norm(ref) || p.id === refId; })[0];
    if (match) {
      origin = { id: match.id, url: match.link, title: match.title };
    } else if (refId && ids.indexOf(refId) >= 0) {
      // Came from a post that isn't public yet (an admin preview): link back without a title.
      origin = { id: refId, url: ref, title: '' };
    } else {
      // Moving between reference pages: keep pointing at the story the reader started from.
      var saved = load();
      if (saved && ids.indexOf(saved.id) >= 0 && ref && new URL(ref).origin === location.origin) origin = saved;
    }
    if (origin) { store(origin); render(published, origin); return; }
    // Came from any other page on the site (a character profile, the Bible Characters index,
    // a tag or category list): link back to it by its public title.
    var r = sameSite(ref);
    if (!r) { render(published, null); return; }
    lookup(r).then(function (title) {
      render(published, { url: ref, title: title, kind: 'page' });
    });
  }

  function sameSite(u) {
    try {
      var x = new URL(u);
      if (x.origin !== location.origin || norm(u) === norm(location.href) || /^\/wp-(admin|login)/.test(x.pathname)) return null;
      return x;
    } catch (e) { return null; }
  }
  // Public title for a same-site URL from the REST API (only published content is returned).
  function lookup(x) {
    var seg = x.pathname.split('/').filter(Boolean);
    if (!seg.length) return Promise.resolve('Home');
    function get(path) {
      return fetch('/wp-json/wp/v2/' + path, { credentials: 'omit' })
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (a) { return a && a[0] ? (a[0].title ? a[0].title.rendered : a[0].name) : ''; })
        .catch(function () { return ''; });
    }
    function text(t) { var d = document.createElement('textarea'); d.innerHTML = t; return d.value; }
    var slug = encodeURIComponent(seg[seg.length - 1]);
    var tax = { tag: 'tags', category: 'categories' }[seg[0]];
    var first = tax ? get(tax + '?slug=' + slug + '&_fields=name') : get('pages?slug=' + slug + '&_fields=title');
    return first.then(function (t) { return t || tax ? t : get('posts?slug=' + slug + '&_fields=title'); }).then(text);
  }

  var url = '/wp-json/wp/v2/posts?include=' + ids.join(',') + '&per_page=' + ids.length + '&_fields=id,link,title';
  fetch(url, { credentials: 'omit' })
    .then(function (r) { return r.ok ? r.json() : []; })
    .then(function (list) {
      decide(list.map(function (p) {
        var t = document.createElement('textarea');
        t.innerHTML = p.title.rendered;
        return { id: p.id, link: p.link, title: t.value };
      }));
    })
    .catch(function () { decide([]); });
  }
})();
