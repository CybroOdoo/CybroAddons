/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ===================================================================
   1. FILM GRAIN WIDGET
   =================================================================== */
publicWidget.registry.CineverseGrain = publicWidget.Widget.extend({
    selector: '#grain',

    start: function () {
        this._super.apply(this, arguments);
        if (prefersReduced) return;

        this.canvas = this.el;
        this.ctx = this.canvas.getContext("2d");
        this.frame = 0;

        this._onResize = this._onResize.bind(this);
        this._drawGrain = this._drawGrain.bind(this);

        window.addEventListener("resize", this._onResize, { passive: true });
        this._onResize();
        this._drawGrain();
    },

    destroy: function () {
        if (this.animFrameId) {
            cancelAnimationFrame(this.animFrameId);
        }
        window.removeEventListener("resize", this._onResize);
        this._super.apply(this, arguments);
    },

    _onResize: function () {
        this.w = this.canvas.width = window.innerWidth;
        this.h = this.canvas.height = window.innerHeight;
    },

    _drawGrain: function () {
        if (this.frame % 2 === 0 && this.w && this.h) {
            const img = this.ctx.createImageData(this.w, this.h);
            const buf = new Uint32Array(img.data.buffer);
            const len = buf.length;
            for (let i = 0; i < len; i++) {
                const v = (Math.random() * 255) | 0;
                buf[i] = (Math.random() < 0.45 ? 16 : 0) << 24 | (v << 16) | (v << 8) | v;
            }
            this.ctx.putImageData(img, 0, 0);
        }
        this.frame++;
        this.animFrameId = requestAnimationFrame(this._drawGrain);
    },
});

/* ===================================================================
   2. PRELOADER WIDGET
   =================================================================== */
publicWidget.registry.CineversePreloader = publicWidget.Widget.extend({
    selector: '#preloader',

    start: function () {
        this._super.apply(this, arguments);
        const MIN = prefersReduced ? 100 : 3000;
        const t0 = Date.now();

        const hide = () => {
            const wait = Math.max(0, MIN - (Date.now() - t0));
            setTimeout(() => this.el.classList.add("is-done"), wait);
        };

        if (document.readyState === "complete") {
            hide();
        } else {
            window.addEventListener("load", hide, { once: true });
        }
        setTimeout(() => this.el.classList.add("is-done"), MIN + 5000);
    },
});

/* ===================================================================
   3. NAVBAR & SCROLL PROGRESS WIDGET
   =================================================================== */
publicWidget.registry.CineverseNavbar = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    events: {
        'click #hamburger': '_onHamburgerClick',
        'click #navBackdrop': '_closeMenu',
        'click .nav__link': '_onNavLinkClick',
        'click .nav__cta': '_closeMenu',
        'click #toTop': '_onToTopClick',
        'click a[href^="#"]': '_onAnchorClick',
    },

    start: function () {
        this._super.apply(this, arguments);
        document.body.classList.add("js-enabled");

        this.navbar = document.querySelector("#top");
        this.progress = document.querySelector("#scrollProgress");
        this.toTop = document.querySelector("#toTop");
        this.hamburger = document.querySelector("#hamburger");
        this.navMenu = document.querySelector("#navMenu");
        this.navBackdrop = document.querySelector("#navBackdrop");
        this.navbarEl = document.querySelector("#navbar");

        this._onScroll = this._onScroll.bind(this);
        window.addEventListener("scroll", this._onScroll, { passive: true });
        this._onScroll();

        this._onKeydown = this._onKeydown.bind(this);
        document.addEventListener("keydown", this._onKeydown);

        this._initScrollReveal();
        this._highlightActiveNav();
        this._initYear();
    },

    destroy: function () {
        window.removeEventListener("scroll", this._onScroll);
        document.removeEventListener("keydown", this._onKeydown);
        this._super.apply(this, arguments);
    },

    _initYear: function () {
        const yearEl = document.querySelector("#year");
        if (yearEl) yearEl.textContent = new Date().getFullYear();
    },

    _onScroll: function () {
        const y = window.scrollY;
        const docH = document.documentElement.scrollHeight - window.innerHeight;
        if (this.navbar) this.navbar.classList.toggle("is-scrolled", y > 50);
        if (this.progress) this.progress.style.width = (docH > 0 ? (y / docH) * 100 : 0) + "%";
        if (this.toTop) this.toTop.classList.toggle("is-visible", y > 700);
    },

    _onToTopClick: function () {
        window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" });
    },

    _onHamburgerClick: function () {
        if (!this.navMenu) return;
        const open = this.navMenu.classList.toggle("is-open");
        if (this.hamburger) {
            this.hamburger.classList.toggle("is-open", open);
            this.hamburger.setAttribute("aria-expanded", String(open));
            this.hamburger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
        }
        document.body.style.overflow = open ? "hidden" : "";
        if (this.navbarEl) this.navbarEl.classList.toggle("menu-is-open", open);
        if (this.navBackdrop) this.navBackdrop.classList.toggle("is-open", open);
    },

    _closeMenu: function () {
        if (!this.navMenu) return;
        this.navMenu.classList.remove("is-open");
        if (this.hamburger) {
            this.hamburger.classList.remove("is-open");
            this.hamburger.setAttribute("aria-expanded", "false");
            this.hamburger.setAttribute("aria-label", "Open menu");
        }
        document.body.style.overflow = "";
        if (this.navbarEl) this.navbarEl.classList.remove("menu-is-open");
        if (this.navBackdrop) this.navBackdrop.classList.remove("is-open");
    },

    _onNavLinkClick: function () {
        this._closeMenu();
    },

    _onKeydown: function (ev) {
        if (ev.key === "Escape") this._closeMenu();
    },

    _onAnchorClick: function (ev) {
        const link = ev.currentTarget;
        const id = link.getAttribute("href");
        if (!id || id.length < 2) return;
        const target = document.querySelector(id);
        if (!target) return;
        ev.preventDefault();
        this._closeMenu();
        const offset = (this.navbar ? this.navbar.offsetHeight : 0) + 12;
        window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - offset, behavior: prefersReduced ? "auto" : "smooth" });
    },

    _initScrollReveal: function () {
        const revealEls = Array.from(document.querySelectorAll(".reveal"));
        if ("IntersectionObserver" in window && !prefersReduced) {
            const io = new IntersectionObserver(entries => {
                entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); } });
            }, { threshold: 0.1, rootMargin: "0px 0px -6% 0px" });
            revealEls.forEach(el => io.observe(el));
        } else {
            revealEls.forEach(el => el.classList.add("is-visible"));
        }
    },

    _highlightActiveNav: function () {
        const page = window.location.pathname.split("/").pop() || "index.html";
        document.querySelectorAll(".nav__link").forEach(l => {
            const href = l.getAttribute("href");
            const isHome = (page === "" || page === "index.html") && (href === "index.html" || href === "./");
            l.classList.toggle("is-active", href === page || isHome);
        });
    },
});

/* ===================================================================
   4. HERO BEAM CURSOR WIDGET
   =================================================================== */
publicWidget.registry.CineverseHeroBeam = publicWidget.Widget.extend({
    selector: '#hero',

    start: function () {
        this._super.apply(this, arguments);
        if (prefersReduced) return;

        this.hero = this.el;
        this.tx = window.innerWidth * 0.38;
        this.ty = window.innerHeight * 0.58;
        this.cx = this.tx;
        this.cy = this.ty;
        this.LERP = 0.07;

        this._onMouseMove = this._onMouseMove.bind(this);
        this._animate = this._animate.bind(this);

        this.hero.addEventListener("mousemove", this._onMouseMove);
        this._animate();
    },

    destroy: function () {
        if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
        if (this.hero) this.hero.removeEventListener("mousemove", this._onMouseMove);
        this._super.apply(this, arguments);
    },

    _onMouseMove: function (e) {
        const r = this.hero.getBoundingClientRect();
        this.tx = e.clientX - r.left;
        this.ty = e.clientY - r.top;
    },

    _animate: function () {
        this.cx += (this.tx - this.cx) * this.LERP;
        this.cy += (this.ty - this.cy) * this.LERP;
        this.hero.style.setProperty("--cx", this.cx + "px");
        this.hero.style.setProperty("--cy", this.cy + "px");
        this.animFrameId = requestAnimationFrame(this._animate);
    },
});

/* ===================================================================
   5. FILM STRIP CAROUSEL WIDGET
   =================================================================== */
publicWidget.registry.CineverseFilmStrip = publicWidget.Widget.extend({
    selector: '#filmStrip, .strip-outer',

    events: {
        'click #stripPrev': '_onPrev',
        'click #stripNext': '_onNext',
        'mouseenter': '_onMouseEnter',
        'mouseleave': '_onMouseLeave',
    },

    start: function () {
        this._super.apply(this, arguments);
        this.strip = this.el.id === "filmStrip" ? this.el : this.el.querySelector("#filmStrip");
        if (!this.strip) return;
        this.outer = this.strip.closest(".strip-outer");
        this.prevBtn = document.querySelector("#stripPrev");
        this.nextBtn = document.querySelector("#stripNext");
        this.cards = Array.from(this.strip.querySelectorAll(".film-card"));
        if (!this.cards.length) return;

        this.DELAY = 3500;
        this.current = 0;
        this.paused = false;

        this.dotsEl = document.createElement("div");
        this.dotsEl.className = "strip-dots";
        this.barEl = document.createElement("div"); this.barEl.className = "strip-progress-bar";
        this.fill = document.createElement("div"); this.fill.className = "strip-progress-bar__fill";
        this.barEl.appendChild(this.fill);
        this.outer.insertAdjacentElement("afterend", this.dotsEl);
        this.dotsEl.insertAdjacentElement("afterend", this.barEl);

        this._onTouchStart = this._onTouchStart.bind(this);
        this._onTouchEnd = this._onTouchEnd.bind(this);
        this.outer.addEventListener("touchstart", this._onTouchStart, { passive: true });
        this.outer.addEventListener("touchend", this._onTouchEnd);

        this._onResize = this._onResize.bind(this);
        window.addEventListener("resize", this._onResize);

        this._buildDots();
        this._goTo(0);
        this._runBar();
        this._startTimer();
    },

    destroy: function () {
        this._stopTimer();
        if (this.outer) {
            this.outer.removeEventListener("touchstart", this._onTouchStart);
            this.outer.removeEventListener("touchend", this._onTouchEnd);
        }
        window.removeEventListener("resize", this._onResize);
        this._super.apply(this, arguments);
    },

    _getVisible: function () {
        return window.innerWidth >= 1025 ? 4 : window.innerWidth >= 600 ? 2 : 1;
    },

    _getMax: function () {
        return Math.max(0, this.cards.length - this._getVisible());
    },

    _buildDots: function () {
        this.dotsEl.innerHTML = "";
        this.dots = Array.from({ length: this._getMax() + 1 }, (_, i) => {
            const d = document.createElement("button");
            d.className = "strip-dot" + (i === this.current ? " is-active" : "");
            d.setAttribute("aria-label", "Slide " + (i + 1));
            d.addEventListener("click", () => { this._goTo(i); this._restartTimer(); });
            this.dotsEl.appendChild(d);
            return d;
        });
    },

    _goTo: function (idx) {
        this.current = Math.max(0, Math.min(idx, this._getMax()));
        const gap = parseInt(getComputedStyle(this.strip).gap) || 18;
        const cardW = this.cards[0].offsetWidth;
        this.strip.style.transform = `translateX(-${this.current * (cardW + gap)}px)`;
        if (this.dots) {
            this.dots.forEach((d, i) => d.classList.toggle("is-active", i === this.current));
        }
        if (this.prevBtn) this.prevBtn.disabled = this.current === 0;
        if (this.nextBtn) this.nextBtn.disabled = this.current >= this._getMax();
        this.fill.classList.remove("is-running");
        void this.fill.offsetWidth;
        if (!this.paused) this.fill.classList.add("is-running");
    },

    _startTimer: function () {
        this.timer = setInterval(() => {
            if (!this.paused) this._goTo(this.current >= this._getMax() ? 0 : this.current + 1);
        }, this.DELAY);
    },

    _stopTimer: function () {
        if (this.timer) clearInterval(this.timer);
    },

    _restartTimer: function () {
        this._stopTimer();
        this._startTimer();
    },

    _runBar: function () {
        this.fill.classList.remove("is-running");
        void this.fill.offsetWidth;
        this.fill.classList.add("is-running");
    },

    _onPrev: function () {
        this._goTo(this.current - 1);
        this._restartTimer();
    },

    _onNext: function () {
        this._goTo(this.current + 1);
        this._restartTimer();
    },

    _onMouseEnter: function () {
        this.paused = true;
        this.fill.classList.remove("is-running");
    },

    _onMouseLeave: function () {
        this.paused = false;
        this._runBar();
    },

    _onTouchStart: function (e) {
        this.touchX = e.touches[0].clientX;
    },

    _onTouchEnd: function (e) {
        const dx = e.changedTouches[0].clientX - this.touchX;
        if (Math.abs(dx) > 40) {
            this._goTo(this.current + (dx < 0 ? 1 : -1));
            this._restartTimer();
        }
    },

    _onResize: function () {
        clearTimeout(this.rzTimer);
        this.rzTimer = setTimeout(() => {
            this._buildDots();
            this._goTo(Math.min(this.current, this._getMax()));
        }, 220);
    },
});

/* ===================================================================
   6. BUTTON RIPPLE WIDGET
   =================================================================== */
publicWidget.registry.CineverseRipple = publicWidget.Widget.extend({
    selector: '.btn--ripple',

    events: {
        'click': '_onClick',
    },

    _onClick: function (e) {
        const rect = this.el.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const r = document.createElement("span");
        r.className = "ripple";
        r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left - size / 2}px;top:${e.clientY - rect.top - size / 2}px`;
        this.el.appendChild(r);
        setTimeout(() => r.remove(), 600);
    },
});

/* ===================================================================
   7. SHOWTIME SLOT SELECTION & DATE TABS WIDGET
   =================================================================== */
publicWidget.registry.CineverseShowtimeSlots = publicWidget.Widget.extend({
    selector: '.board__row, .date-tab',

    events: {
        'click .time-btn': '_onTimeBtnClick',
        'click': '_onDateTabClick',
    },

    _onTimeBtnClick: function (ev) {
        const btn = ev.currentTarget;
        const row = btn.closest(".board__row");
        if (row) {
            row.querySelectorAll(".time-btn").forEach(b => b.classList.remove("time-btn--lit"));
            btn.classList.add("time-btn--lit");
        }
    },

    _onDateTabClick: function () {
        if (this.el.classList.contains("date-tab")) {
            document.querySelectorAll(".date-tab").forEach(t => t.classList.remove("is-active"));
            this.el.classList.add("is-active");
        }
    },
});

/* ===================================================================
   8. VIP TICKET 3D TILT & QR CANVAS WIDGET
   =================================================================== */
publicWidget.registry.CineverseTicket3D = publicWidget.Widget.extend({
    selector: '#memberTicket',

    events: {
        'mousemove': '_onMouseMove',
        'mouseleave': '_onMouseLeave',
    },

    start: function () {
        this._super.apply(this, arguments);
        this._drawQR();
    },

    _onMouseMove: function (e) {
        if (prefersReduced || !window.matchMedia("(pointer:fine)").matches) return;
        const r = this.el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        this.el.style.transform = `perspective(900px) rotateY(${px * 10}deg) rotateX(${-py * 8}deg)`;
    },

    _onMouseLeave: function () {
        this.el.style.transform = "";
    },

    _drawQR: function () {
        const qr = document.querySelector("#ticketQR");
        if (!qr) return;
        const ctx = qr.getContext("2d");
        const S = 72, CELL = 6, COLS = S / CELL;
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
    },
});

/* ===================================================================
   9. GALLERY LIGHTBOX WIDGET
   =================================================================== */
publicWidget.registry.CineverseLightbox = publicWidget.Widget.extend({
    selector: '#lightbox',

    events: {
        'click #lbClose': '_onClose',
        'click #lbPrev': '_onPrev',
        'click #lbNext': '_onNext',
        'click': '_onBackdropClick',
    },

    start: function () {
        this._super.apply(this, arguments);
        this.lbImg = this.el.querySelector("#lbImg");
        this.lbCap = this.el.querySelector("#lbCaption");
        this.galItems = Array.from(document.querySelectorAll(".gal-item:not([aria-hidden])"));

        if (this.galItems.length) {
            this.srcs = this.galItems.map(f => f.dataset.full || f.querySelector("img").src);
            this.caps = this.galItems.map(f => f.dataset.caption || "");
            this.cur = 0;

            this.galItems.forEach((f, i) => f.addEventListener("click", () => this._lbOpen(i)));
        }

        this._onKeydown = this._onKeydown.bind(this);
        document.addEventListener("keydown", this._onKeydown);
    },

    destroy: function () {
        document.removeEventListener("keydown", this._onKeydown);
        this._super.apply(this, arguments);
    },

    _lbShow: function (i) {
        if (!this.srcs || !this.srcs.length) return;
        this.cur = (i + this.srcs.length) % this.srcs.length;
        if (this.lbImg) {
            this.lbImg.src = this.srcs[this.cur];
            this.lbImg.alt = this.caps[this.cur];
        }
        if (this.lbCap) this.lbCap.textContent = this.caps[this.cur];
    },

    _lbOpen: function (i) {
        this._lbShow(i);
        this.el.classList.add("is-open");
        this.el.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    },

    _onClose: function () {
        this.el.classList.remove("is-open");
        this.el.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    },

    _onPrev: function () {
        this._lbShow(this.cur - 1);
    },

    _onNext: function () {
        this._lbShow(this.cur + 1);
    },

    _onBackdropClick: function (e) {
        if (e.target === this.el) this._onClose();
    },

    _onKeydown: function (e) {
        if (!this.el.classList.contains("is-open")) return;
        if (e.key === "Escape") this._onClose();
        if (e.key === "ArrowRight") this._lbShow(this.cur + 1);
        if (e.key === "ArrowLeft") this._lbShow(this.cur - 1);
    },
});

/* ===================================================================
   10. TESTIMONIAL CAROUSEL WIDGET
   =================================================================== */
publicWidget.registry.CineverseTestimonials = publicWidget.Widget.extend({
    selector: '#carousel',

    events: {
        'mouseenter': '_stop',
        'mouseleave': '_start',
    },

    start: function () {
        this._super.apply(this, arguments);
        this.track = this.el.querySelector("#carouselTrack");
        this.dotsWrap = this.el.querySelector("#carouselDots");
        if (!this.track || !this.dotsWrap) return;

        this.slides = Array.from(this.track.querySelectorAll(".testimonial"));
        this.idx = 0;

        this.slides.forEach((_, i) => {
            const d = document.createElement("button");
            d.setAttribute("role", "tab");
            d.setAttribute("aria-label", `Testimonial ${i + 1}`);
            if (i === 0) d.classList.add("is-active");
            d.addEventListener("click", () => this._goTo(i, true));
            this.dotsWrap.appendChild(d);
        });
        this.dots = Array.from(this.dotsWrap.querySelectorAll("button"));

        this._onTouchStart = this._onTouchStart.bind(this);
        this._onTouchEnd = this._onTouchEnd.bind(this);
        this.el.addEventListener("touchstart", this._onTouchStart, { passive: true });
        this.el.addEventListener("touchend", this._onTouchEnd);

        this._start();
    },

    destroy: function () {
        this._stop();
        this._super.apply(this, arguments);
    },

    _goTo: function (i, manual = false) {
        if (!this.slides || !this.slides.length) return;
        this.idx = (i + this.slides.length) % this.slides.length;
        this.track.style.transform = `translateX(-${this.idx * 100}%)`;
        if (this.dots) {
            this.dots.forEach((d, di) => d.classList.toggle("is-active", di === this.idx));
        }
        if (manual) this._restart();
    },

    _start: function () {
        if (!prefersReduced && !this.timer) {
            this.timer = setInterval(() => this._goTo(this.idx + 1), 5500);
        }
    },

    _stop: function () {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    },

    _restart: function () {
        this._stop();
        this._start();
    },

    _onTouchStart: function (e) {
        this.sx = e.touches[0].clientX;
        this._stop();
    },

    _onTouchEnd: function (e) {
        const dx = e.changedTouches[0].clientX - this.sx;
        if (Math.abs(dx) > 50) this._goTo(this.idx + (dx < 0 ? 1 : -1), true);
        else this._start();
    },
});

/* ===================================================================
   11. TRAILER MODAL WIDGET
   =================================================================== */
publicWidget.registry.CineverseTrailerModal = publicWidget.Widget.extend({
    selector: '#trailerModal, #wrapwrap',

    events: {
        'click #trailerBtn': '_openModal',
        'click #trailerModal [data-close]': '_closeModal',
    },

    start: function () {
        this._super.apply(this, arguments);
        this.modal = document.querySelector("#trailerModal");
        this._onKeydown = this._onKeydown.bind(this);
        document.addEventListener("keydown", this._onKeydown);
    },

    destroy: function () {
        document.removeEventListener("keydown", this._onKeydown);
        this._super.apply(this, arguments);
    },

    _openModal: function () {
        if (!this.modal) return;
        this.modal.classList.add("is-open");
        this.modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    },

    _closeModal: function () {
        if (!this.modal) return;
        this.modal.classList.remove("is-open");
        this.modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    },

    _onKeydown: function (e) {
        if (e.key === "Escape" && this.modal && this.modal.classList.contains("is-open")) {
            this._closeModal();
        }
    },
});

/* ===================================================================
   12. BOOKING MODAL WIDGET
   =================================================================== */
publicWidget.registry.CineverseBookingModal = publicWidget.Widget.extend({
    selector: '#bookingModal, #wrapwrap',

    events: {
        'click #bookingClose': '_closeModal',
        'click #bDone': '_closeModal',
        'click #bNext1': '_onNext1',
        'click #bBack2': '_onBack2',
        'click #bPay': '_onPay',
        'click .board__row .time-btn': '_onShowtimeTimeClick',
        'input #bCard': '_formatCard',
        'input #bExpiry': '_formatExpiry',
        'click': '_onModalClick',
    },

    start: function () {
        this._super.apply(this, arguments);
        this.modal = document.querySelector("#bookingModal");
        this.ROWS = "ABCDEFGHIJ".split("");
        this.VIP_ROWS = ["A", "B"];
        this.COLS = 12;

        this.FILMS = {
            "Celestial Drift": { screen: "SCREEN 1 · IMAX", price: 22, vip: 44 },
            "The Velvet Hour": { screen: "SCREEN 2 · PREMIERE", price: 20, vip: 40 },
            "Midnight Sonata": { screen: "SCREEN 3 · DOLBY ATMOS", price: 22, vip: 42 },
            "Golden Empire": { screen: "SCREEN 4 · 4K LASER", price: 20, vip: 40 },
            "The Last Frame": { screen: "SCREEN 5 · DIRECTOR'S CUT", price: 18, vip: 36 }
        };

        this.TAKEN = {
            "Celestial Drift": "A3 A8 B2 B7 C4 C10 D1 D6 D11 E5 E9 F3 F8 G2 G7 H5 H11 I4 I9 J3".split(" "),
            "The Velvet Hour": "A1 A6 B4 B9 C2 C7 D5 D10 E3 E8 F1 F6 F11 G4 G9 H2 H7 I5 I10 J8".split(" "),
            "Midnight Sonata": "A2 A9 B5 B11 C3 C8 D4 D9 E1 E7 F5 F10 G3 G8 H1 H6 H12 I3 I8 J6".split(" "),
            "Golden Empire": "A4 A10 B1 B6 C5 C9 D2 D8 E4 E10 F2 F7 G5 G11 H3 H8 I2 I7 J4 J10".split(" "),
            "The Last Frame": "A5 A11 B3 B8 C1 C6 D3 D7 E2 E6 E12 F4 F9 G2 G7 H4 H10 I1 I6 J9".split(" ")
        };

        this.selected = [];

        this._onKeydown = this._onKeydown.bind(this);
        document.addEventListener("keydown", this._onKeydown);
    },

    destroy: function () {
        document.removeEventListener("keydown", this._onKeydown);
        this._super.apply(this, arguments);
    },

    _onShowtimeTimeClick: function (ev) {
        const btn = ev.currentTarget;
        const row = btn.closest(".board__row");
        const h3 = row ? row.querySelector("h3") : null;
        const film = h3 ? h3.textContent.trim() : "";
        const time = btn.textContent.trim();

        if (row) {
            row.querySelectorAll(".time-btn").forEach(b => b.classList.remove("time-btn--lit"));
            btn.classList.add("time-btn--lit");
        }
        this._openModal(film, time);
    },

    _openModal: function (film, time) {
        if (!this.modal) return;
        this.currentFilm = film;
        this.currentTime = time;
        this.currentInfo = this.FILMS[film] || { screen: "", price: 20, vip: 40 };
        this.selected = [];

        const bFilm = document.querySelector("#bFilm");
        const bScreen = document.querySelector("#bScreen");
        if (bFilm) bFilm.textContent = film;
        if (bScreen) bScreen.textContent = this.currentInfo.screen + "  ·  " + time;

        this._buildSeatMap();
        this._updateBar();
        this._goStep(1);

        this.modal.classList.add("is-open");
        this.modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    },

    _closeModal: function () {
        if (!this.modal) return;
        this.modal.classList.remove("is-open");
        this.modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    },

    _onModalClick: function (e) {
        if (e.target === this.modal) this._closeModal();
    },

    _onKeydown: function (e) {
        if (e.key === "Escape" && this.modal && this.modal.classList.contains("is-open")) {
            this._closeModal();
        }
    },

    _buildSeatMap: function () {
        const map = document.querySelector("#seatMap");
        if (!map) return;
        map.innerHTML = "";
        const wrap = document.createElement("div");
        wrap.className = "seat-rows";
        const takenSet = {};
        (this.TAKEN[this.currentFilm] || []).forEach(id => { takenSet[id] = true; });

        this.ROWS.forEach(row => {
            const rowEl = document.createElement("div");
            rowEl.className = "seat-row";

            const lbl = document.createElement("span");
            lbl.className = "seat-row__lbl";
            lbl.textContent = row;
            rowEl.appendChild(lbl);

            for (let c = 1; c <= this.COLS; c++) {
                if (c === 7) {
                    const gap = document.createElement("span");
                    gap.className = "seat-row__aisle";
                    rowEl.appendChild(gap);
                }
                const id = row + c;
                const isTaken = !!takenSet[id];
                const isVip = this.VIP_ROWS.indexOf(row) !== -1;
                const seat = document.createElement("button");
                seat.type = "button";
                seat.className = "seat" + (isVip ? " seat--vip" : "") + (isTaken ? " seat--taken" : "");
                seat.textContent = c;
                seat.dataset.id = id;
                seat.dataset.vip = isVip ? "1" : "";
                seat.setAttribute("aria-label", "Seat " + id + (isVip ? " VIP" : "") + (isTaken ? " — unavailable" : ""));
                if (isTaken) {
                    seat.disabled = true;
                } else {
                    seat.addEventListener("click", ev => this._onSeatClick(ev, seat));
                }
                rowEl.appendChild(seat);
            }
            wrap.appendChild(rowEl);
        });
        map.appendChild(wrap);
    },

    _onSeatClick: function (ev, seatEl) {
        const id = seatEl.dataset.id;
        const idx = this.selected.indexOf(id);
        if (idx === -1) {
            if (this.selected.length >= 8) return;
            this.selected.push(id);
            seatEl.classList.add("seat--sel");
        } else {
            this.selected.splice(idx, 1);
            seatEl.classList.remove("seat--sel");
        }
        this._updateBar();
    },

    _isVipSeat: function (id) {
        return this.VIP_ROWS.indexOf(id[0]) !== -1;
    },

    _calcTotal: function () {
        return this.selected.reduce((sum, id) => {
            return sum + (this._isVipSeat(id) ? this.currentInfo.vip : this.currentInfo.price);
        }, 0);
    },

    _updateBar: function () {
        const sorted = this.selected.slice().sort();
        const bSeatList = document.querySelector("#bSeatList");
        const bTotal = document.querySelector("#bTotal");
        const bNext1 = document.querySelector("#bNext1");

        if (bSeatList) bSeatList.textContent = sorted.length ? sorted.join(", ") : "—";
        if (bTotal) bTotal.textContent = "£" + this._calcTotal();
        if (bNext1) bNext1.disabled = this.selected.length === 0;
    },

    _goStep: function (n) {
        [1, 2, 3].forEach(i => {
            const pane = document.getElementById("bPane" + i);
            const step = this.modal ? this.modal.querySelector(".bk-step[data-step='" + i + "']") : null;
            if (pane) pane.hidden = (i !== n);
            if (step) {
                step.classList.toggle("is-active", i === n);
                step.classList.toggle("is-done", i < n);
            }
        });
        const panel = this.modal ? this.modal.querySelector(".booking-modal__panel") : null;
        if (panel) panel.scrollTop = 0;
    },

    _onNext1: function () {
        if (!this.selected.length) return;
        this._fillOrderBox();
        this._goStep(2);
    },

    _fillOrderBox: function () {
        const sorted = this.selected.slice().sort();
        const std = sorted.filter(id => !this._isVipSeat(id));
        const vip = sorted.filter(id => this._isVipSeat(id));
        let html = "";
        if (std.length) html += '<div class="bk-order-row"><span>Standard &times; ' + std.length + '</span><span>&pound;' + (std.length * this.currentInfo.price) + '</span></div>';
        if (vip.length) html += '<div class="bk-order-row"><span>VIP &times; ' + vip.length + '</span><span>&pound;' + (vip.length * this.currentInfo.vip) + '</span></div>';
        html += '<div class="bk-order-row"><span>Seats</span><span>' + sorted.join(", ") + '</span></div>';
        html += '<div class="bk-order-row"><span>Showtime</span><span>' + this.currentTime + '</span></div>';
        html += '<div class="bk-order-row bk-order-row--total"><span>Total</span><span>&pound;' + this._calcTotal() + '</span></div>';
        const orderBox = document.querySelector("#bOrderBox");
        if (orderBox) orderBox.innerHTML = html;
    },

    _onBack2: function () {
        this._goStep(1);
    },

    _onPay: function () {
        const nameEl = document.querySelector("#bName");
        const emailEl = document.querySelector("#bEmail");
        const cardEl = document.querySelector("#bCard");
        const expiryEl = document.querySelector("#bExpiry");
        const cvvEl = document.querySelector("#bCvv");
        const errEl = document.querySelector("#bError");

        const name = (nameEl ? nameEl.value : "").trim();
        const email = (emailEl ? emailEl.value : "").trim();
        const card = (cardEl ? cardEl.value : "").trim();
        const expiry = (expiryEl ? expiryEl.value : "").trim();
        const cvv = (cvvEl ? cvvEl.value : "").trim();

        if (!name) { if (errEl) errEl.textContent = "Please enter your full name."; return; }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { if (errEl) errEl.textContent = "Please enter a valid email address."; return; }
        if (!/^[\d ]{15,19}$/.test(card)) { if (errEl) errEl.textContent = "Please enter a valid card number."; return; }
        if (!/^\d{2}\s*\/\s*\d{2}$/.test(expiry)) { if (errEl) errEl.textContent = "Please enter expiry as MM / YY."; return; }
        if (!/^\d{3,4}$/.test(cvv)) { if (errEl) errEl.textContent = "Please enter a valid CVV."; return; }
        if (errEl) errEl.textContent = "";

        const ref = "CV-" + Math.random().toString(36).substring(2, 8).toUpperCase();
        this._buildTicket(name, email, ref);
        this._saveBooking(name, email, ref);
        this._goStep(3);
    },

    _buildTicket: function (name, email, ref) {
        const sorted = this.selected.slice().sort();
        const bTicket = document.querySelector("#bTicket");
        if (bTicket) {
            bTicket.innerHTML =
                '<div class="bt-ref">' + ref + '</div>' +
                '<div class="bt-row"><span>FILM</span><span>' + this.currentFilm + '</span></div>' +
                '<div class="bt-row"><span>SCREEN</span><span>' + (this.currentInfo.screen || "") + '</span></div>' +
                '<div class="bt-row"><span>SHOWTIME</span><span>' + this.currentTime + '</span></div>' +
                '<div class="bt-row"><span>SEATS</span><span>' + sorted.join(", ") + '</span></div>' +
                '<div class="bt-row"><span>GUEST</span><span>' + name + '</span></div>' +
                '<div class="bt-row"><span>EMAIL</span><span>' + email + '</span></div>' +
                '<div class="bt-row bt-total"><span>TOTAL PAID</span><span>&pound;' + this._calcTotal() + '</span></div>';
        }
    },

    _saveBooking: function (name, email, ref) {
        const sorted = this.selected.slice().sort();
        const booking = {
            ref: ref,
            film: this.currentFilm,
            screen: this.currentInfo.screen || "",
            time: this.currentTime,
            seats: sorted,
            total: this._calcTotal(),
            name: name,
            email: email,
            bookedAt: new Date().toISOString()
        };
        const all = JSON.parse(localStorage.getItem("cv_bookings") || "[]");
        all.unshift(booking);
        localStorage.setItem("cv_bookings", JSON.stringify(all));

        window.dispatchEvent(new CustomEvent("cv_booking_updated"));
    },

    _formatCard: function (ev) {
        const input = ev.currentTarget;
        let v = input.value.replace(/\D/g, "").slice(0, 16);
        input.value = v.replace(/(.{4})/g, "$1 ").trim();
    },

    _formatExpiry: function (ev) {
        const input = ev.currentTarget;
        let v = input.value.replace(/\D/g, "").slice(0, 4);
        if (v.length > 2) v = v.slice(0, 2) + " / " + v.slice(2);
        input.value = v;
    },
});

/* ===================================================================
   13. BOOKINGS DRAWER WIDGET
   =================================================================== */
publicWidget.registry.CineverseBookingsDrawer = publicWidget.Widget.extend({
    selector: '#bookingsDrawer, #wrapwrap',

    events: {
        'click #ticketBtn': '_toggleDrawer',
        'click #bookingsClose': '_closeDrawer',
        'click #bookingsBackdrop': '_closeDrawer',
    },

    start: function () {
        this._super.apply(this, arguments);
        this.ticketBtn = document.querySelector("#ticketBtn");
        this.ticketBadge = document.querySelector("#ticketBadge");
        this.drawer = document.querySelector("#bookingsDrawer");
        this.drawerClose = document.querySelector("#bookingsClose");
        this.drawerBody = document.querySelector("#bookingsBody");
        this.drawerBackdrop = document.querySelector("#bookingsBackdrop");

        this._renderDrawer = this._renderDrawer.bind(this);
        window.addEventListener("cv_booking_updated", this._renderDrawer);
        window.addEventListener("storage", ev => {
            if (ev.key === "cv_bookings") this._renderDrawer();
        });

        this._onKeydown = this._onKeydown.bind(this);
        document.addEventListener("keydown", this._onKeydown);

        this._renderDrawer();
    },

    destroy: function () {
        window.removeEventListener("cv_booking_updated", this._renderDrawer);
        document.removeEventListener("keydown", this._onKeydown);
        this._super.apply(this, arguments);
    },

    _renderDrawer: function () {
        const bookings = JSON.parse(localStorage.getItem("cv_bookings") || "[]");
        const count = bookings.length;

        if (this.ticketBadge && this.ticketBtn) {
            if (count > 0) {
                this.ticketBadge.textContent = count > 99 ? "99+" : String(count);
                this.ticketBadge.hidden = false;
                this.ticketBtn.classList.add("has-tickets");
            } else {
                this.ticketBadge.hidden = true;
                this.ticketBtn.classList.remove("has-tickets");
            }
        }

        if (!this.drawerBody) return;
        if (count === 0) {
            this.drawerBody.innerHTML =
                '<div class="bookings-empty">' +
                '<div class="bookings-empty__icon">🎟</div>' +
                '<p>NO BOOKINGS YET<br>YOUR TICKETS WILL<br>APPEAR HERE</p>' +
                '</div>';
            return;
        }

        let html = "";
        bookings.forEach(b => {
            let dateStr = "";
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
        this.drawerBody.innerHTML = html;
    },

    _toggleDrawer: function () {
        if (this.drawer && this.drawer.classList.contains("is-open")) {
            this._closeDrawer();
        } else {
            this._openDrawer();
        }
    },

    _openDrawer: function () {
        if (!this.drawer) return;
        this._renderDrawer();
        this.drawer.classList.add("is-open");
        this.drawer.setAttribute("aria-hidden", "false");
        if (this.ticketBtn) this.ticketBtn.setAttribute("aria-expanded", "true");
        if (this.drawerBackdrop) this.drawerBackdrop.classList.add("is-open");
        document.body.style.overflow = "hidden";
    },

    _closeDrawer: function () {
        if (!this.drawer) return;
        this.drawer.classList.remove("is-open");
        this.drawer.setAttribute("aria-hidden", "true");
        if (this.ticketBtn) this.ticketBtn.setAttribute("aria-expanded", "false");
        if (this.drawerBackdrop) this.drawerBackdrop.classList.remove("is-open");
        document.body.style.overflow = "";
    },

    _onKeydown: function (e) {
        if (e.key === "Escape" && this.drawer && this.drawer.classList.contains("is-open")) {
            this._closeDrawer();
        }
    },
});
