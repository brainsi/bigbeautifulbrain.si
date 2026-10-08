/* Big Beautiful Brain: site interactions. Vanilla JS, no dependencies. */
(function () {
  'use strict';
  var doc = document.documentElement;
  doc.classList.add('js');
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- header state ---------- */
  var header = document.querySelector('.site-header');
  function onScroll() {
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- menu overlay ---------- */
  var menu = document.getElementById('menu');
  var openers = document.querySelectorAll('[data-menu-open]');
  var closers = document.querySelectorAll('[data-menu-close]');
  var lastFocus = null;
  function openMenu() {
    if (!menu) return;
    lastFocus = document.activeElement;
    menu.classList.add('is-open');
    menu.setAttribute('aria-hidden', 'false');
    document.body.classList.add('menu-open');
    openers.forEach(function (b) { b.setAttribute('aria-expanded', 'true'); });
    var first = menu.querySelector('[data-menu-close]');
    if (first) setTimeout(function () { first.focus(); }, 60);
  }
  function closeMenu() {
    if (!menu) return;
    menu.classList.remove('is-open');
    menu.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('menu-open');
    openers.forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  openers.forEach(function (b) { b.addEventListener('click', openMenu); });
  closers.forEach(function (b) { b.addEventListener('click', closeMenu); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menu && menu.classList.contains('is-open')) closeMenu();
    if (e.key === 'Tab' && menu && menu.classList.contains('is-open')) {
      var f = menu.querySelectorAll('a[href], button:not([disabled])');
      f = Array.prototype.filter.call(f, function (el) { return el.offsetParent !== null; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  // detail panel: hovering or focusing a group shows its detail
  var groupButtons = document.querySelectorAll('[data-detail]');
  function showDetail(id) {
    document.querySelectorAll('.menu-detail [data-panel]').forEach(function (p) { p.hidden = p.getAttribute('data-panel') !== id; });
    groupButtons.forEach(function (b) { b.setAttribute('aria-expanded', b.getAttribute('data-detail') === id ? 'true' : 'false'); });
  }
  groupButtons.forEach(function (b) {
    b.addEventListener('mouseenter', function () { showDetail(b.getAttribute('data-detail')); });
    b.addEventListener('focus', function () { showDetail(b.getAttribute('data-detail')); });
    b.addEventListener('click', function () { showDetail(b.getAttribute('data-detail')); });
  });
  if (groupButtons.length) showDetail(groupButtons[0].getAttribute('data-detail'));

  /* ---------- reveal on scroll ---------- */
  var revealEls = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* ---------- hero: living neural graph ---------- */
  var hero = document.querySelector('.hero');
  var canvas = document.querySelector('.brain-canvas');
  var toggle = document.querySelector('.motion-toggle');
  var running = !reduceMotion;
  if (canvas && canvas.getContext) {
    var ctx = canvas.getContext('2d');
    var W = 0, H = 0, DPR = 1, nodes = [], edges = [], pulses = [], t0 = performance.now();
    var LABELS = ['Customers', 'Operations', 'Finance', 'People', 'Vendors', 'Product', 'Sales', 'Systems', 'Risks', 'Processes', 'Contracts', 'KPIs', 'Partners', 'Pricing'];
    function seed() {
      var mobile = W < 760;
      var count = Math.round(Math.max(44, Math.min(120, (W * H) / (mobile ? 9000 : 14500))));
      var cx = W * 0.71, cy = H * 0.44, rx = W * 0.265, ry = H * 0.36;
      // narrow screens: the copy spans the full width, so keep the brain in the band between the header and the copy
      var copy = W < 1000 && hero && hero.querySelector('.hero-copy');
      if (copy) {
        var top = 88, bottom = copy.getBoundingClientRect().top - canvas.getBoundingClientRect().top + 4;
        cx = W * 0.5; cy = top + (bottom - top) / 2; rx = W * 0.44; ry = Math.max(56, (bottom - top) / 2);
      }
      nodes = [];
      for (var i = 0; i < count; i++) {
        var a = Math.random() * Math.PI * 2, r = Math.pow(Math.random(), 0.7);
        // two lobes, so the cloud reads as a brain rather than a disc
        var lobe = i % 2 === 0 ? -1 : 1;
        var x = cx + lobe * rx * 0.18 + Math.cos(a) * rx * 0.82 * r;
        var y = cy + Math.sin(a) * ry * r * (0.92 + 0.08 * Math.cos(a * 2));
        nodes.push({ x: x, y: y, ox: x, oy: y, vx: 0, vy: 0, r: 1.3 + Math.random() * 2.1, ph: Math.random() * 6.28, label: i < LABELS.length ? LABELS[i] : null });
      }
      // drop any label that would overlap another or leave the canvas; boxes are padded for the drift
      ctx.font = '600 11px Inter, -apple-system, sans-serif';
      var boxes = [];
      nodes.forEach(function (n) {
        if (!n.label) return;
        var w = ctx.measureText(n.label.toUpperCase()).width;
        var b = [n.ox - 4, n.oy - 32, n.ox + 22 + w, n.oy + 8];
        var clash = b[2] > W - 8 || b[1] < 80 || boxes.some(function (o) { return b[0] < o[2] && b[2] > o[0] && b[1] < o[3] && b[3] > o[1]; });
        if (clash) n.label = null; else boxes.push(b);
      });
      edges = [];
      var maxD = Math.min(W, H) * (mobile ? 0.17 : 0.13);
      for (var p = 0; p < nodes.length; p++) {
        for (var q = p + 1; q < nodes.length; q++) {
          var dx = nodes[p].ox - nodes[q].ox, dy = nodes[p].oy - nodes[q].oy;
          var d = Math.sqrt(dx * dx + dy * dy);
          if (d < maxD) edges.push([p, q, d / maxD]);
        }
      }
      pulses = [];
    }
    function resize() {
      DPR = Math.min(window.devicePixelRatio || 1, 2);
      W = canvas.clientWidth; H = canvas.clientHeight;
      canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      seed();
      draw(performance.now(), true);
    }
    function spawnPulse() {
      if (!edges.length) return;
      var e = edges[(Math.random() * edges.length) | 0];
      var dir = Math.random() < 0.5;
      pulses.push({ a: dir ? e[0] : e[1], b: dir ? e[1] : e[0], t: 0, s: 0.006 + Math.random() * 0.01 });
    }
    function draw(now, still) {
      var time = (now - t0) / 1000;
      ctx.clearRect(0, 0, W, H);
      var i, n;
      for (i = 0; i < nodes.length; i++) {
        n = nodes[i];
        if (!still) {
          n.x = n.ox + Math.cos(time * 0.35 + n.ph) * 6 + Math.sin(time * 0.21 + n.ph * 2) * 4;
          n.y = n.oy + Math.sin(time * 0.3 + n.ph) * 5;
        }
      }
      ctx.lineWidth = 1;
      for (i = 0; i < edges.length; i++) {
        var e = edges[i], A = nodes[e[0]], B = nodes[e[1]];
        ctx.strokeStyle = 'rgba(11,27,43,' + (0.16 * (1 - e[2]) + 0.02).toFixed(3) + ')';
        ctx.beginPath(); ctx.moveTo(A.x, A.y); ctx.lineTo(B.x, B.y); ctx.stroke();
      }
      if (!still) {
        if (pulses.length < 26 && Math.random() < 0.35) spawnPulse();
        for (i = pulses.length - 1; i >= 0; i--) {
          var P = pulses[i]; P.t += P.s;
          if (P.t >= 1) { pulses.splice(i, 1); if (Math.random() < 0.55) { var nb = edges.filter(function (ed) { return ed[0] === P.b || ed[1] === P.b; }); if (nb.length) { var ne = nb[(Math.random() * nb.length) | 0]; pulses.push({ a: P.b, b: ne[0] === P.b ? ne[1] : ne[0], t: 0, s: P.s }); } } continue; }
          var a1 = nodes[P.a], b1 = nodes[P.b];
          var px = a1.x + (b1.x - a1.x) * P.t, py = a1.y + (b1.y - a1.y) * P.t;
          var g = ctx.createRadialGradient(px, py, 0, px, py, 9);
          g.addColorStop(0, 'rgba(36,190,140,0.95)'); g.addColorStop(1, 'rgba(36,190,140,0)');
          ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, py, 9, 0, 6.283); ctx.fill();
        }
      }
      for (i = 0; i < nodes.length; i++) {
        n = nodes[i];
        ctx.fillStyle = n.label ? 'rgba(11,27,43,0.88)' : 'rgba(11,27,43,0.55)';
        ctx.beginPath(); ctx.arc(n.x, n.y, n.label ? n.r + 1.4 : n.r, 0, 6.283); ctx.fill();
        if (n.label && W > 760) {
          var alpha = 0.35 + 0.45 * (0.5 + 0.5 * Math.sin(time * 0.6 + n.ph));
          ctx.font = '600 11px Inter, -apple-system, sans-serif';
          ctx.fillStyle = 'rgba(11,27,43,' + alpha.toFixed(2) + ')';
          ctx.fillText(n.label.toUpperCase(), n.x + 8, n.y - 7);
        }
      }
    }
    var raf = 0;
    function loop(now) { draw(now, false); raf = requestAnimationFrame(loop); }
    function start() { if (!raf) raf = requestAnimationFrame(loop); }
    function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
    var heroVisible = true;
    if ('IntersectionObserver' in window && hero) {
      new IntersectionObserver(function (en) { heroVisible = en[0].isIntersecting; if (heroVisible && running) start(); else stop(); }).observe(hero);
    }
    window.addEventListener('resize', function () { clearTimeout(resize._t); resize._t = setTimeout(resize, 150); });
    resize();
    // web fonts change the height of the copy, and the narrow layout places the brain from it
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(resize);
    if (running) start();
    if (toggle) {
      var setToggle = function () {
        toggle.setAttribute('aria-pressed', running ? 'false' : 'true');
        toggle.setAttribute('aria-label', running ? 'Pause background motion' : 'Play background motion');
        toggle.innerHTML = running
          ? '<svg viewBox="0 0 14 14"><rect x="3" y="2" width="2.6" height="10" rx="1" fill="#0b1b2b"/><rect x="8.4" y="2" width="2.6" height="10" rx="1" fill="#0b1b2b"/></svg>'
          : '<svg viewBox="0 0 14 14"><path d="M4 2.5v9l7.5-4.5z" fill="#0b1b2b"/></svg>';
        if (hero) hero.classList.toggle('is-paused', !running);
      };
      toggle.addEventListener('click', function () { running = !running; if (running && heroVisible) start(); else stop(); setToggle(); });
      setToggle();
    }
  }

  /* ---------- tabs ---------- */
  document.querySelectorAll('[data-tabs]').forEach(function (wrap) {
    var tabs = wrap.querySelectorAll('[role="tab"]');
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute('aria-controls'));
        if (panel) {
          panel.hidden = !on;
          if (on) { panel.classList.remove('is-entering'); void panel.offsetWidth; panel.classList.add('is-entering'); }
        }
      });
      if (focus) tab.focus();
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(t, false); });
      t.addEventListener('keydown', function (e) {
        var k = e.key, j = i;
        if (k === 'ArrowRight') j = (i + 1) % tabs.length;
        else if (k === 'ArrowLeft') j = (i - 1 + tabs.length) % tabs.length;
        else if (k === 'Home') j = 0;
        else if (k === 'End') j = tabs.length - 1;
        else return;
        e.preventDefault(); select(tabs[j], true);
      });
    });
  });

  /* ---------- sticky steps ---------- */
  document.querySelectorAll('[data-steps]').forEach(function (wrap) {
    var steps = wrap.querySelectorAll('.step');
    var imgs = wrap.querySelectorAll('.steps-visual img');
    var badge = wrap.querySelector('.steps-visual .badge');
    var bar = wrap.querySelector('.steps-visual .progress i');
    function activate(i) {
      steps.forEach(function (s, k) { s.classList.toggle('is-active', k === i); });
      imgs.forEach(function (im, k) { im.classList.toggle('is-active', k === i); });
      if (badge) badge.textContent = steps[i].getAttribute('data-badge') || '';
      if (bar) bar.style.width = ((i + 1) / steps.length * 100) + '%';
    }
    if ('IntersectionObserver' in window) {
      var so = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) activate(Array.prototype.indexOf.call(steps, en.target)); });
      }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
      steps.forEach(function (s) { so.observe(s); });
    }
    activate(0);
  });

  /* ---------- carousel ---------- */
  document.querySelectorAll('[data-carousel]').forEach(function (car) {
    var slides = car.querySelectorAll('.slide');
    var dotsWrap = car.querySelector('.dots');
    var idx = 0, timer = 0;
    slides.forEach(function (s, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Show question ' + (i + 1));
      b.addEventListener('click', function () { go(i); restart(); });
      dotsWrap.appendChild(b);
    });
    var dots = dotsWrap.querySelectorAll('button');
    function go(i) {
      idx = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('is-active', k === idx); s.setAttribute('aria-hidden', k === idx ? 'false' : 'true'); });
      dots.forEach(function (d, k) { d.setAttribute('aria-current', k === idx ? 'true' : 'false'); });
    }
    function restart() { clearInterval(timer); if (!reduceMotion) timer = setInterval(function () { go(idx + 1); }, 6500); }
    var prev = car.querySelector('[data-prev]'), next = car.querySelector('[data-next]');
    if (prev) prev.addEventListener('click', function () { go(idx - 1); restart(); });
    if (next) next.addEventListener('click', function () { go(idx + 1); restart(); });
    car.addEventListener('mouseenter', function () { clearInterval(timer); });
    car.addEventListener('mouseleave', restart);
    go(0); restart();
  });

  /* ---------- counters ---------- */
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length && 'IntersectionObserver' in window) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target, target = parseFloat(el.getAttribute('data-count')), start = performance.now(), dur = reduceMotion ? 1 : 1400;
        (function tick(now) {
          var p = Math.min(1, (now - start) / dur), v = Math.round(target * (1 - Math.pow(1 - p, 3)));
          el.textContent = v.toLocaleString('en-US');
          if (p < 1) requestAnimationFrame(tick);
        })(start);
        co.unobserve(el);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (c) { co.observe(c); });
  }

  /* ---------- contact form: sends through FormSubmit to the inbox in data-email ---------- */
  var form = document.querySelector('[data-contact-form]');
  if (form) {
    var formStatus = form.querySelector('.form-status');
    var formButton = form.querySelector('button[type="submit"]');
    var inbox = form.getAttribute('data-email');
    var say = function (html, kind) {
      formStatus.hidden = false;
      formStatus.className = 'form-status' + (kind ? ' is-' + kind : '');
      formStatus.innerHTML = html;
    };
    form.addEventListener('submit', function (e) {
      // without fetch the plain POST to the action URL still works and lands on thanks.html
      if (!window.fetch || !window.FormData) return;
      e.preventDefault();
      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = v; });
      if (data._honey) return; // only bots fill the hidden field
      delete data._next;
      data._subject = 'Website enquiry: ' + (data.firm || data.name || 'Big Beautiful Brain');
      formButton.disabled = true;
      formButton.setAttribute('aria-busy', 'true');
      say('Sending your message...');
      fetch(form.getAttribute('data-endpoint'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(data)
      }).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok || String(j.success) !== 'true') throw new Error(j.message || 'HTTP ' + r.status);
        });
      }).then(function () {
        form.reset();
        say('Thank you. Your message has reached our team, and we will reply by email.', 'ok');
      }).catch(function () {
        say('We could not send your message just now. Please email <a class="link" href="mailto:' + inbox + '">' + inbox + '</a> and we will reply from there.', 'error');
      }).then(function () {
        formButton.disabled = false;
        formButton.removeAttribute('aria-busy');
      });
    });
  }

  /* ---------- section nav follows the section in view ---------- */
  var subnav = document.querySelector('.subnav');
  if (subnav) {
    var spyLinks = Array.prototype.slice.call(subnav.querySelectorAll('a[href^="#"]'));
    var spyItems = spyLinks.map(function (a) { return { a: a, el: document.getElementById(a.getAttribute('href').slice(1)) }; }).filter(function (x) { return x.el; });
    var spyTick = false;
    var updateSpy = function () {
      spyTick = false;
      var line = window.innerHeight * 0.4, current = spyItems[0];
      spyItems.forEach(function (x) { if (x.el.getBoundingClientRect().top <= line) current = x; });
      spyItems.forEach(function (x) { x.a.classList.toggle('is-current', x === current); });
    };
    window.addEventListener('scroll', function () { if (!spyTick) { spyTick = true; requestAnimationFrame(updateSpy); } }, { passive: true });
    updateSpy();
  }

  /* ---------- footer year ---------- */
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
