/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CineverseCore = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start: function () {
        document.body.classList.add("js-enabled");
        const $ = (sel, ctx = document) => ctx.querySelector(sel);
        const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
        const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;


  /* ===================================================================
     FILM GRAIN — animated noise on a fixed canvas
     =================================================================== */
  (function initGrain() {
    const canvas = $("#grain");
    if (!canvas || prefersReduced) return;
    const ctx = canvas.getContext("2d");
    let w, h, frame = 0;

    function resize() {
      w = canvas.width  = window.innerWidth;
      h = canvas.height = window.innerHeight;
    }
    function drawGrain() {
      if (frame % 2 === 0) {            // update every other frame → 30fps grain
        const img  = ctx.createImageData(w, h);
        const buf  = new Uint32Array(img.data.buffer);
        const len  = buf.length;
        for (let i = 0; i < len; i++) {
          const v = (Math.random() * 255) | 0;
          buf[i]  = (Math.random() < 0.45 ? 16 : 0) << 24 | (v << 16) | (v << 8) | v;
        }
        ctx.putImageData(img, 0, 0);
      }
      frame++;
      requestAnimationFrame(drawGrain);
    }
    window.addEventListener("resize", resize, { passive: true });
    resize();
    drawGrain();
  })();

  /* ===================================================================
     PRELOADER — hold for countdown (3·2·1) to complete
     =================================================================== */
  (function initPreloader() {
    const el  = $("#preloader");
    if (!el) return;
    const MIN = prefersReduced ? 100 : 3000;   // ms — covers 3×0.65s + gap + brand reveal
    const t0  = Date.now();
    function hide() {
      const wait = Math.max(0, MIN - (Date.now() - t0));
      setTimeout(() => el.classList.add("is-done"), wait);
    }
    if (document.readyState === "complete") hide();
    else window.addEventListener("load", hide);
    setTimeout(() => el.classList.add("is-done"), MIN + 5000); // safety net
  })();

  /* ===================================================================
     YEAR
     =================================================================== */
  const yearEl = $("#year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ===================================================================
     SCROLL PROGRESS + BACK-TO-TOP + NAVBAR SCROLL STATE
     =================================================================== */
  const navbar   = $("#top");
  const progress = $("#scrollProgress");
  const toTop    = $("#toTop");

  function onScroll() {
    const y    = window.scrollY;
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    if (navbar)   navbar.classList.toggle("is-scrolled", y > 50);
    if (progress) progress.style.width = (docH > 0 ? (y / docH) * 100 : 0) + "%";
    if (toTop)    toTop.classList.toggle("is-visible", y > 700);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" }));

  /* ===================================================================
     PROJECTOR BEAM CURSOR — smooth lerp follows mouse in hero
     =================================================================== */
  (function initBeam() {
    const hero = $("#hero");
    if (!hero || prefersReduced) return;
    let tx = window.innerWidth * 0.38, ty = window.innerHeight * 0.58;
    let cx = tx, cy = ty;
    const LERP = 0.07;

    hero.addEventListener("mousemove", e => {
      const r = hero.getBoundingClientRect();
      tx = e.clientX - r.left;
      ty = e.clientY - r.top;
    });

    function animate() {
      cx += (tx - cx) * LERP;
      cy += (ty - cy) * LERP;
      hero.style.setProperty("--cx", cx + "px");
      hero.style.setProperty("--cy", cy + "px");
      requestAnimationFrame(animate);
    }
    animate();
  })();

  /* ===================================================================
     MOBILE MENU
     =================================================================== */
  const hamburger   = $("#hamburger");
  const navMenu     = $("#navMenu");
  const navBackdrop = $("#navBackdrop");
  const navbarEl    = $("#top");
  const navClose    = $("#navClose");

  function closeMenu() {
    if (!navMenu) return;
    navMenu.classList.remove("is-open");
    if (hamburger) {
      hamburger.classList.remove("is-open");
      hamburger.setAttribute("aria-expanded", "false");
      hamburger.setAttribute("aria-label", "Open menu");
    }
    document.body.style.overflow = "";
    document.documentElement.style.overflow = "";
    document.body.classList.remove("menu-open");
    document.documentElement.classList.remove("menu-open");
    if (navbarEl)   navbarEl.classList.remove("menu-is-open");
    if (navBackdrop) navBackdrop.classList.remove("is-open");
  }

  if (hamburger && navMenu) {
    hamburger.addEventListener("click", () => {
      const open = navMenu.classList.toggle("is-open");
      hamburger.classList.toggle("is-open", open);
      hamburger.setAttribute("aria-expanded", String(open));
      hamburger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      document.body.style.overflow = open ? "hidden" : "";
      document.documentElement.style.overflow = open ? "hidden" : "";
      document.body.classList.toggle("menu-open", open);
      document.documentElement.classList.toggle("menu-open", open);
      if (navbarEl)   navbarEl.classList.toggle("menu-is-open", open);
      if (navBackdrop) navBackdrop.classList.toggle("is-open", open);
    });
    if (navClose) navClose.addEventListener("click", closeMenu);
    if (navBackdrop) navBackdrop.addEventListener("click", closeMenu);
    $$(".nav__link, .nav__cta, .dropdown-item", navMenu).forEach(l => {
      l.addEventListener("click", () => {
        if (l.classList.contains("dropdown-toggle") || l.getAttribute("data-bs-toggle") === "dropdown") {
          return;
        }
        closeMenu();
      });
    });
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeMenu(); });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 1140 && navMenu.classList.contains("is-open")) {
        closeMenu();
      }
    }, { passive: true });
  }

  /* ===================================================================
     SMOOTH ANCHOR SCROLL (with nav offset)
     =================================================================== */
  $$('a[href^="#"]').forEach(link => {
    link.addEventListener("click", e => {
      const id = link.getAttribute("href");
      if (!id || id.length < 2) return;
      const target = $(id);
      if (!target) return;
      e.preventDefault();
      closeMenu();
      const offset = (navbar ? navbar.offsetHeight : 0) + 12;
      window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - offset, behavior: prefersReduced ? "auto" : "smooth" });
    });
  });

  /* ===================================================================
     SCROLL REVEAL + ACTIVE NAV LINK
     =================================================================== */
  const revealEls = $$(".reveal");
  if ("IntersectionObserver" in window && !prefersReduced) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); } });
    }, { threshold: 0.1, rootMargin: "0px 0px -6% 0px" });
    revealEls.forEach(el => io.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add("is-visible"));
  }

  // Multi-page: set active nav link by matching current filename
  const page = window.location.pathname.split("/").pop() || "index.html";
  $$(".nav__link").forEach(l => {
    const href = l.getAttribute("href");
    const isHome = (page === "" || page === "index.html") && (href === "index.html" || href === "./");
    l.classList.toggle("is-active", href === page || isHome);
  });

  /* ===================================================================
     FILM STRIP — 4-up transform carousel
     =================================================================== */
  (function initStrip() {
    const strip   = $("#filmStrip");
    if (!strip) return;
    const outer   = strip.closest(".strip-outer");
    const prevBtn = $("#stripPrev");
    const nextBtn = $("#stripNext");
    const cards   = Array.from(strip.querySelectorAll(".film-card"));
    const DELAY   = 3500;
    let current   = 0, timer = null, paused = false;

    /* Dots + progress bar — injected AFTER strip-outer */
    const dotsEl = document.createElement("div");
    dotsEl.className = "strip-dots";
    const barEl  = document.createElement("div");  barEl.className  = "strip-progress-bar";
    const fill   = document.createElement("div");  fill.className   = "strip-progress-bar__fill";
    barEl.appendChild(fill);
    outer.insertAdjacentElement("afterend", dotsEl);
    dotsEl.insertAdjacentElement("afterend", barEl);

    function getVisible() {
      return window.innerWidth >= 1025 ? 4 : window.innerWidth >= 600 ? 2 : 1;
    }
    function getMax() { return Math.max(0, cards.length - getVisible()); }

    let dots = [];
    function buildDots() {
      dotsEl.innerHTML = "";
      dots = Array.from({ length: getMax() + 1 }, (_, i) => {
        const d = document.createElement("button");
        d.className = "strip-dot" + (i === current ? " is-active" : "");
        d.setAttribute("aria-label", "Slide " + (i + 1));
        d.addEventListener("click", () => { goTo(i); restartTimer(); });
        dotsEl.appendChild(d);
        return d;
      });
    }

    function goTo(idx) {
      current = Math.max(0, Math.min(idx, getMax()));
      const gap  = parseInt(getComputedStyle(strip).gap) || 18;
      const cardW = cards[0].offsetWidth;
      strip.style.transform = `translateX(-${current * (cardW + gap)}px)`;
      dots.forEach((d, i) => d.classList.toggle("is-active", i === current));
      if (prevBtn) prevBtn.disabled = current === 0;
      if (nextBtn) nextBtn.disabled = current >= getMax();
      fill.classList.remove("is-running");
      void fill.offsetWidth;
      if (!paused) fill.classList.add("is-running");
    }

    function startTimer() {
      timer = setInterval(() => {
        if (!paused) goTo(current >= getMax() ? 0 : current + 1);
      }, DELAY);
    }
    function restartTimer() { clearInterval(timer); startTimer(); }
    function runBar() { fill.classList.remove("is-running"); void fill.offsetWidth; fill.classList.add("is-running"); }

    if (prevBtn) prevBtn.addEventListener("click", () => { goTo(current - 1); restartTimer(); });
    if (nextBtn) nextBtn.addEventListener("click", () => { goTo(current + 1); restartTimer(); });

    /* Pause on hover */
    outer.addEventListener("mouseenter", () => { paused = true;  fill.classList.remove("is-running"); });
    outer.addEventListener("mouseleave", () => { paused = false; runBar(); });

    /* Touch swipe */
    let tx = 0;
    outer.addEventListener("touchstart", e => { tx = e.touches[0].clientX; }, { passive: true });
    outer.addEventListener("touchend",   e => {
      const dx = e.changedTouches[0].clientX - tx;
      if (Math.abs(dx) > 40) { goTo(current + (dx < 0 ? 1 : -1)); restartTimer(); }
    });

    /* Rebuild on resize */
    let rzTimer;
    window.addEventListener("resize", () => {
      clearTimeout(rzTimer);
      rzTimer = setTimeout(() => { buildDots(); goTo(Math.min(current, getMax())); }, 220);
    });

    buildDots();
    goTo(0);
    runBar();
    startTimer();
  })();

  /* ===================================================================
     BUTTON RIPPLE
     =================================================================== */
  $$(".btn--ripple").forEach(btn => {
    btn.addEventListener("click", function (e) {
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const r    = document.createElement("span");
      r.className = "ripple";
      r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left - size / 2}px;top:${e.clientY - rect.top - size / 2}px`;
      this.appendChild(r);
      setTimeout(() => r.remove(), 600);
    });
  });

  /* ===================================================================
     SHOWTIME SLOT SELECTION
     =================================================================== */
  $$(".time-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      const row = this.closest(".board__row");
      $$(".time-btn", row).forEach(b => b.classList.remove("time-btn--lit"));
      this.classList.add("time-btn--lit");
    });
  });

  /* ===================================================================
     VIP TICKET — 3D mouse tilt + QR canvas draw
     =================================================================== */
  (function initTicket() {
    const ticket = $("#memberTicket");
    if (ticket && !prefersReduced && window.matchMedia("(pointer:fine)").matches) {
      ticket.addEventListener("mousemove", e => {
        const r  = ticket.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width  - 0.5;
        const py = (e.clientY - r.top)  / r.height - 0.5;
        ticket.style.transform = `perspective(900px) rotateY(${px * 10}deg) rotateX(${-py * 8}deg)`;
      });
      ticket.addEventListener("mouseleave", () => { ticket.style.transform = ""; });
    }

    // Draw a simple QR-like pattern on the canvas
    const qr = $("#ticketQR");
    if (!qr) return;
    const ctx = qr.getContext("2d");
    const S   = 72, CELL = 6, COLS = S / CELL;
    // seed with a fixed pattern that looks like a QR
    const pattern = [
      1,1,1,1,1,1,1,0,1,0,1,1,1,
      1,0,0,0,0,0,1,0,0,1,1,0,1,
      1,0,1,1,1,0,1,0,1,0,0,1,0,
      1,0,1,1,1,0,1,0,0,1,1,0,1,
      1,0,1,1,1,0,1,0,1,1,0,0,1,
      1,0,0,0,0,0,1,0,0,0,1,1,0,
      1,1,1,1,1,1,1,0,1,0,1,0,1,
      0,0,0,0,0,0,0,0,1,1,0,1,0,
      1,0,1,1,0,1,1,0,1,0,1,1,1,
      0,1,0,1,1,0,0,1,0,1,0,1,0,
      1,1,1,0,1,1,1,0,1,0,1,0,1,
      0,1,0,1,0,1,0,1,0,1,0,1,0,
      1,0,1,0,1,0,1,0,1,0,1,0,1,
    ];
    ctx.fillStyle = "#070A13";
    ctx.fillRect(0, 0, S, S);
    ctx.fillStyle = "#C9A84C";
    pattern.forEach((v, i) => {
      if (!v) return;
      const col = i % COLS, row = Math.floor(i / COLS);
      ctx.fillRect(col * CELL, row * CELL, CELL - 1, CELL - 1);
    });
  })();

  /* ===================================================================
     GALLERY LIGHTBOX — click on .gal-item (non-duplicate only)
     =================================================================== */
  const lbEl    = $("#lightbox");
  const lbImg   = $("#lbImg");
  const lbCap   = $("#lbCaption");
  const lbClose = $("#lbClose");
  const lbPrev  = $("#lbPrev");
  const lbNext  = $("#lbNext");
  const galItems = $$(".gal-item:not([aria-hidden])");

  if (lbEl && lbImg) {
    const srcs = galItems.map(f => f.dataset.full || f.querySelector("img").src);
    const caps = galItems.map(f => f.dataset.caption || "");
    let cur = 0;

    function lbShow(i) {
      cur = (i + srcs.length) % srcs.length;
      lbImg.src = srcs[cur];
      lbImg.alt = caps[cur];
      if (lbCap) lbCap.textContent = caps[cur];
    }
    function lbOpen(i) {
      lbShow(i); lbEl.classList.add("is-open");
      lbEl.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    }
    function lbClose_() {
      lbEl.classList.remove("is-open");
      lbEl.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }

    galItems.forEach((f, i) => f.addEventListener("click", () => lbOpen(i)));
    if (lbClose) lbClose.addEventListener("click", lbClose_);
    if (lbPrev)  lbPrev.addEventListener("click",  () => lbShow(cur - 1));
    if (lbNext)  lbNext.addEventListener("click",  () => lbShow(cur + 1));
    lbEl.addEventListener("click", e => { if (e.target === lbEl) lbClose_(); });
    document.addEventListener("keydown", e => {
      if (!lbEl.classList.contains("is-open")) return;
      if (e.key === "Escape")      lbClose_();
      if (e.key === "ArrowRight")  lbShow(cur + 1);
      if (e.key === "ArrowLeft")   lbShow(cur - 1);
    });
  }

  /* ===================================================================
     TESTIMONIAL CAROUSEL
     =================================================================== */
  (function initCarousel() {
    const track    = $("#carouselTrack");
    const dotsWrap = $("#carouselDots");
    if (!track || !dotsWrap) return;

    const slides = $$(".testimonial", track);
    let idx = 0, timer = null;

    slides.forEach((_, i) => {
      const d = document.createElement("button");
      d.setAttribute("role", "tab");
      d.setAttribute("aria-label", `Testimonial ${i + 1}`);
      if (i === 0) d.classList.add("is-active");
      d.addEventListener("click", () => goTo(i, true));
      dotsWrap.appendChild(d);
    });
    const dots = $$("button", dotsWrap);

    function goTo(i, manual = false) {
      idx = (i + slides.length) % slides.length;
      track.style.transform = `translateX(-${idx * 100}%)`;
      dots.forEach((d, di) => d.classList.toggle("is-active", di === idx));
      if (manual) restart();
    }
    function start() { if (!prefersReduced) timer = setInterval(() => goTo(idx + 1), 5500); }
    function stop()  { clearInterval(timer); }
    function restart() { stop(); start(); }

    const carousel = $("#carousel");
    carousel.addEventListener("mouseenter", stop);
    carousel.addEventListener("mouseleave", start);

    let sx = 0;
    carousel.addEventListener("touchstart", e => { sx = e.touches[0].clientX; stop(); }, { passive: true });
    carousel.addEventListener("touchend",   e => {
      const dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 50) goTo(idx + (dx < 0 ? 1 : -1), true);
      else start();
    });
    start();
  })();

  /* ===================================================================
     TRAILER MODAL
     =================================================================== */
  const trailerBtn  = $("#trailerBtn");
  const trailerModal = $("#trailerModal");
  if (trailerBtn && trailerModal) {
    const openModal  = () => { trailerModal.classList.add("is-open"); trailerModal.setAttribute("aria-hidden","false"); document.body.style.overflow="hidden"; };
    const closeModal = () => { trailerModal.classList.remove("is-open"); trailerModal.setAttribute("aria-hidden","true"); document.body.style.overflow=""; };
    trailerBtn.addEventListener("click", openModal);
    $$("[data-close]", trailerModal).forEach(el => el.addEventListener("click", closeModal));
    document.addEventListener("keydown", e => { if (e.key === "Escape" && trailerModal.classList.contains("is-open")) closeModal(); });
  }



  /* ===================================================================
     DATE TABS — showtimes page
     =================================================================== */
  $$(".date-tab").forEach(tab => {
    tab.addEventListener("click", function () {
      $$(".date-tab").forEach(t => t.classList.remove("is-active"));
      this.classList.add("is-active");
    });
  });


/* ===================================================================
   BOOKING MODAL — seat selection · details · confirmation
   =================================================================== */
(function initBooking() {
  var modal = $("#bookingModal");
  if (!modal) return;

  var ROWS     = "ABCDEFGHIJ".split("");
  var VIP_ROWS = ["A", "B"];
  var COLS     = 12;

  var FILMS = {
    "Celestial Drift": { screen: "SCREEN 1 · IMAX",           price: 22, vip: 44 },
    "The Velvet Hour":  { screen: "SCREEN 2 · PREMIERE",       price: 20, vip: 40 },
    "Midnight Sonata":  { screen: "SCREEN 3 · DOLBY ATMOS",    price: 22, vip: 42 },
    "Golden Empire":    { screen: "SCREEN 4 · 4K LASER",       price: 20, vip: 40 },
    "The Last Frame":   { screen: "SCREEN 5 · DIRECTOR'S CUT", price: 18, vip: 36 }
  };

  var TAKEN = {
    "Celestial Drift": "A3 A8 B2 B7 C4 C10 D1 D6 D11 E5 E9 F3 F8 G2 G7 H5 H11 I4 I9 J3".split(" "),
    "The Velvet Hour":  "A1 A6 B4 B9 C2 C7 D5 D10 E3 E8 F1 F6 F11 G4 G9 H2 H7 I5 I10 J8".split(" "),
    "Midnight Sonata":  "A2 A9 B5 B11 C3 C8 D4 D9 E1 E7 F5 F10 G3 G8 H1 H6 H12 I3 I8 J6".split(" "),
    "Golden Empire":    "A4 A10 B1 B6 C5 C9 D2 D8 E4 E10 F2 F7 G5 G11 H3 H8 I2 I7 J4 J10".split(" "),
    "The Last Frame":   "A5 A11 B3 B8 C1 C6 D3 D7 E2 E6 E12 F4 F9 G2 G7 H4 H10 I1 I6 J9".split(" ")
  };

  var currentFilm = "", currentTime = "", currentInfo = {};
  var selected = [];

  /* ---- open / close ---- */
  function openModal(film, time) {
    currentFilm = film;
    currentTime = time;
    currentInfo = FILMS[film] || { screen: "", price: 20, vip: 40 };
    selected    = [];

    $("#bFilm").textContent   = film;
    $("#bScreen").textContent = currentInfo.screen + "  ·  " + time;

    buildSeatMap();
    updateBar();
    goStep(1);

    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  /* ---- seat map ---- */
  function buildSeatMap() {
    var map = $("#seatMap");
    map.innerHTML = "";
    var wrap = document.createElement("div");
    wrap.className = "seat-rows";
    var takenSet = {};
    (TAKEN[currentFilm] || []).forEach(function (id) { takenSet[id] = true; });

    ROWS.forEach(function (row) {
      var rowEl = document.createElement("div");
      rowEl.className = "seat-row";

      var lbl = document.createElement("span");
      lbl.className   = "seat-row__lbl";
      lbl.textContent = row;
      rowEl.appendChild(lbl);

      for (var c = 1; c <= COLS; c++) {
        if (c === 7) {
          var gap = document.createElement("span");
          gap.className = "seat-row__aisle";
          rowEl.appendChild(gap);
        }
        var id      = row + c;
        var isTaken = !!takenSet[id];
        var isVip   = VIP_ROWS.indexOf(row) !== -1;
        var seat    = document.createElement("button");
        seat.type        = "button";
        seat.className   = "seat" + (isVip ? " seat--vip" : "") + (isTaken ? " seat--taken" : "");
        seat.textContent = c;
        seat.dataset.id  = id;
        seat.dataset.vip = isVip ? "1" : "";
        seat.setAttribute("aria-label", "Seat " + id + (isVip ? " VIP" : "") + (isTaken ? " — unavailable" : ""));
        if (isTaken) {
          seat.disabled = true;
        } else {
          seat.addEventListener("click", onSeatClick);
        }
        rowEl.appendChild(seat);
      }
      wrap.appendChild(rowEl);
    });
    map.appendChild(wrap);
  }

  function onSeatClick() {
    var id  = this.dataset.id;
    var idx = selected.indexOf(id);
    if (idx === -1) {
      if (selected.length >= 8) return;
      selected.push(id);
      this.classList.add("seat--sel");
    } else {
      selected.splice(idx, 1);
      this.classList.remove("seat--sel");
    }
    updateBar();
  }

  function isVipSeat(id) { return VIP_ROWS.indexOf(id[0]) !== -1; }

  function calcTotal() {
    return selected.reduce(function (sum, id) {
      return sum + (isVipSeat(id) ? currentInfo.vip : currentInfo.price);
    }, 0);
  }

  function updateBar() {
    var sorted = selected.slice().sort();
    $("#bSeatList").textContent = sorted.length ? sorted.join(", ") : "—";
    $("#bTotal").textContent    = "£" + calcTotal();
    $("#bNext1").disabled       = selected.length === 0;
  }

  /* ---- step navigation ---- */
  function goStep(n) {
    [1, 2, 3].forEach(function (i) {
      var pane = document.getElementById("bPane" + i);
      var step = modal.querySelector(".bk-step[data-step='" + i + "']");
      if (pane) pane.hidden = (i !== n);
      if (step) {
        step.classList.toggle("is-active", i === n);
        step.classList.toggle("is-done",   i < n);
      }
    });
    var panel = modal.querySelector(".booking-modal__panel");
    if (panel) panel.scrollTop = 0;
  }

  /* ---- step 1 → 2 ---- */
  $("#bNext1").addEventListener("click", function () {
    if (!selected.length) return;
    fillOrderBox();
    goStep(2);
  });

  function fillOrderBox() {
    var sorted = selected.slice().sort();
    var std    = sorted.filter(function (id) { return !isVipSeat(id); });
    var vip    = sorted.filter(function (id) { return  isVipSeat(id); });
    var html   = "";
    if (std.length) html += '<div class="bk-order-row"><span>Standard &times; ' + std.length + '</span><span>&pound;' + (std.length * currentInfo.price) + '</span></div>';
    if (vip.length) html += '<div class="bk-order-row"><span>VIP &times; '      + vip.length + '</span><span>&pound;' + (vip.length * currentInfo.vip)   + '</span></div>';
    html += '<div class="bk-order-row"><span>Seats</span><span>'    + sorted.join(", ") + '</span></div>';
    html += '<div class="bk-order-row"><span>Showtime</span><span>' + currentTime       + '</span></div>';
    html += '<div class="bk-order-row bk-order-row--total"><span>Total</span><span>&pound;' + calcTotal() + '</span></div>';
    $("#bOrderBox").innerHTML = html;
  }

  /* ---- step 2 back ---- */
  $("#bBack2").addEventListener("click", function () { goStep(1); });

  /* ---- step 2 → 3 ---- */
  $("#bPay").addEventListener("click", function () {
    var name   = ($("#bName").value   || "").trim();
    var email  = ($("#bEmail").value  || "").trim();
    var card   = ($("#bCard").value   || "").trim();
    var expiry = ($("#bExpiry").value || "").trim();
    var cvv    = ($("#bCvv").value    || "").trim();
    var errEl  = $("#bError");

    if (!name)                                       { errEl.textContent = "Please enter your full name.";              return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))  { errEl.textContent = "Please enter a valid email address.";       return; }
    if (!/^[\d ]{15,19}$/.test(card))               { errEl.textContent = "Please enter a valid card number.";         return; }
    if (!/^\d{2}\s*\/\s*\d{2}$/.test(expiry))       { errEl.textContent = "Please enter expiry as MM / YY.";           return; }
    if (!/^\d{3,4}$/.test(cvv))                     { errEl.textContent = "Please enter a valid CVV.";                 return; }
    errEl.textContent = "";

    var ref = "CV-" + Math.random().toString(36).substring(2, 8).toUpperCase();
    buildTicket(name, email, ref);
    saveBooking(name, email, ref);
    goStep(3);
  });

  function buildTicket(name, email, ref) {
    var sorted = selected.slice().sort();
    $("#bTicket").innerHTML =
      '<div class="bt-ref">' + ref + '</div>' +
      '<div class="bt-row"><span>FILM</span><span>'     + currentFilm              + '</span></div>' +
      '<div class="bt-row"><span>SCREEN</span><span>'   + (currentInfo.screen||"") + '</span></div>' +
      '<div class="bt-row"><span>SHOWTIME</span><span>' + currentTime              + '</span></div>' +
      '<div class="bt-row"><span>SEATS</span><span>'    + sorted.join(", ")        + '</span></div>' +
      '<div class="bt-row"><span>GUEST</span><span>'    + name                     + '</span></div>' +
      '<div class="bt-row"><span>EMAIL</span><span>'    + email                    + '</span></div>' +
      '<div class="bt-row bt-total"><span>TOTAL PAID</span><span>&pound;' + calcTotal() + '</span></div>';
  }

  function saveBooking(name, email, ref) {
    var sorted = selected.slice().sort();
    var booking = {
      ref:    ref,
      film:   currentFilm,
      screen: currentInfo.screen || "",
      time:   currentTime,
      seats:  sorted,
      total:  calcTotal(),
      name:   name,
      email:  email,
      bookedAt: new Date().toISOString()
    };
    var all = JSON.parse(localStorage.getItem("cv_bookings") || "[]");
    all.unshift(booking);
    localStorage.setItem("cv_bookings", JSON.stringify(all));
    if (typeof window.cvUpdateBadge === "function") window.cvUpdateBadge();
  }

  /* ---- close handlers ---- */
  $("#bookingClose").addEventListener("click", closeModal);
  $("#bDone").addEventListener("click", closeModal);
  modal.addEventListener("click", function (e) { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.classList.contains("is-open")) closeModal();
  });

  /* ---- card / expiry auto-format ---- */
  $("#bCard").addEventListener("input", function () {
    var v = this.value.replace(/\D/g, "").slice(0, 16);
    this.value = v.replace(/(.{4})/g, "$1 ").trim();
  });
  $("#bExpiry").addEventListener("input", function () {
    var v = this.value.replace(/\D/g, "").slice(0, 4);
    if (v.length > 2) v = v.slice(0, 2) + " / " + v.slice(2);
    this.value = v;
  });

  /* ---- wire time buttons ---- */
  [].slice.call($$(".board__row")).forEach(function (row) {
    var h3   = row.querySelector("h3");
    var film = h3 ? h3.textContent.trim() : "";
    [].slice.call(row.querySelectorAll(".time-btn")).forEach(function (btn) {
      btn.addEventListener("click", function () {
        [].slice.call(row.querySelectorAll(".time-btn")).forEach(function (b) { b.classList.remove("time-btn--lit"); });
        this.classList.add("time-btn--lit");
        openModal(film, this.textContent.trim());
      });
    });
  });

})();

/* ===================================================================
   BOOKINGS DRAWER — ticket icon in navbar, persisted in localStorage
   =================================================================== */
(function initBookingsDrawer() {
  var ticketBtn      = $("#ticketBtn");
  var ticketBadge    = $("#ticketBadge");
  var drawer         = $("#bookingsDrawer");
  var drawerClose    = $("#bookingsClose");
  var drawerBody     = $("#bookingsBody");
  var drawerBackdrop = $("#bookingsBackdrop");

  if (!ticketBtn || !drawer) return;

  /* ---- badge + card rendering ---- */
  function renderDrawer() {
    var bookings = JSON.parse(localStorage.getItem("cv_bookings") || "[]");

    // badge
    var count = bookings.length;
    if (count > 0) {
      ticketBadge.textContent = count > 99 ? "99+" : String(count);
      ticketBadge.hidden = false;
      ticketBtn.classList.add("has-tickets");
    } else {
      ticketBadge.hidden = true;
      ticketBtn.classList.remove("has-tickets");
    }

    // drawer body
    if (!drawerBody) return;
    if (count === 0) {
      drawerBody.innerHTML =
        '<div class="bookings-empty">' +
          '<div class="bookings-empty__icon">🎟</div>' +
          '<p>NO BOOKINGS YET<br>YOUR TICKETS WILL<br>APPEAR HERE</p>' +
        '</div>';
      return;
    }

    var html = "";
    bookings.forEach(function (b) {
      var dateStr = "";
      try { dateStr = new Date(b.bookedAt).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }); } catch (e) {}
      html +=
        '<div class="booking-card">' +
          '<div class="booking-card__top">' +
            '<p class="booking-card__ref">' + b.ref + '</p>' +
            '<p class="booking-card__film">' + b.film + '</p>' +
            '<p class="booking-card__meta">' +
              (b.screen ? b.screen + '<br>' : '') +
              b.time + (dateStr ? '  ·  ' + dateStr : '') +
            '</p>' +
          '</div>' +
          '<div class="booking-card__footer">' +
            '<span class="booking-card__seats">Seats: ' + b.seats.join(", ") + '</span>' +
            '<span class="booking-card__price">&pound;' + b.total + '</span>' +
          '</div>' +
        '</div>';
    });
    drawerBody.innerHTML = html;
  }

  /* ---- expose so booking IIFE can call after save ---- */
  window.cvUpdateBadge = renderDrawer;

  /* ---- open / close ---- */
  function openDrawer() {
    renderDrawer();
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    ticketBtn.setAttribute("aria-expanded", "true");
    if (drawerBackdrop) drawerBackdrop.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }

  function closeDrawer() {
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    ticketBtn.setAttribute("aria-expanded", "false");
    if (drawerBackdrop) drawerBackdrop.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  ticketBtn.addEventListener("click", function () {
    if (drawer.classList.contains("is-open")) { closeDrawer(); } else { openDrawer(); }
  });
  if (drawerClose)    drawerClose.addEventListener("click", closeDrawer);
  if (drawerBackdrop) drawerBackdrop.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && drawer.classList.contains("is-open")) closeDrawer();
  });

  /* ---- sync badge across tabs ---- */
  window.addEventListener("storage", function (e) {
    if (e.key === "cv_bookings") renderDrawer();
  });

  /* ---- init badge on page load ---- */
  renderDrawer();
})();

        return this._super.apply(this, arguments);
    }
});
