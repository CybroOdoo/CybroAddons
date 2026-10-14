/** @odoo-module **/

const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function isEditorMode() {
    try {
        return document.body.classList.contains("editor_enable") || 
               document.body.classList.contains("editor_has_snippets") ||
               window.location.search.includes("enable_editor") ||
               !!document.querySelector(".editor_enable") ||
               !!document.querySelector(".o_we_website_top_actions") ||
               (window.top && window.top !== window && (
                   window.top.document.body.classList.contains("editor_enable") || 
                   !!window.top.document.querySelector(".o_we_website_top_actions")
               ));
    } catch {
        return false;
    }
}

function initCineverse() {
    initPreloader();
    initGrain();
    initNavbar();
    initHeroBeam();
    initFilmStrip();
    initRipple();
    initShowtimeSlots();
    initTicket3D();
    initLightbox();
    initTestimonials();
    initTrailerModal();
    initBookingModal();
    initBookingsDrawer();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCineverse);
} else {
    initCineverse();
}

/* ===================================================================
   1. PRELOADER
   =================================================================== */
function initPreloader() {
    const preloader = document.querySelector("#preloader");
    if (!preloader) return;

    if (isEditorMode()) {
        preloader.remove();
        return;
    }

    const MIN = prefersReduced ? 100 : 2600;
    const t0 = Date.now();

    const hide = () => {
        const wait = Math.max(0, MIN - (Date.now() - t0));
        setTimeout(() => {
            preloader.classList.add("is-done");
            setTimeout(() => {
                if (preloader.parentNode) {
                    preloader.style.display = "none";
                }
            }, 700);
        }, wait);
    };

    if (document.readyState === "complete") {
        hide();
    } else {
        window.addEventListener("load", hide, { once: true });
    }
    // Absolute fallback safety timeout
    setTimeout(() => {
        preloader.classList.add("is-done");
        setTimeout(() => {
            if (preloader.parentNode) {
                preloader.style.display = "none";
            }
        }, 700);
    }, MIN + 1500);
}

/* ===================================================================
   2. FILM GRAIN
   =================================================================== */
function initGrain() {
    const canvas = document.querySelector("#grain");
    if (!canvas || prefersReduced || isEditorMode()) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    let animFrameId;
    let w = 0;
    let h = 0;

    const onResize = () => {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    };

    const drawGrain = () => {
        if (frame % 2 === 0 && w && h) {
            const img = ctx.createImageData(w, h);
            const buf = new Uint32Array(img.data.buffer);
            const len = buf.length;
            for (let i = 0; i < len; i++) {
                const v = (Math.random() * 255) | 0;
                buf[i] = (Math.random() < 0.45 ? 16 : 0) << 24 | (v << 16) | (v << 8) | v;
            }
            ctx.putImageData(img, 0, 0);
        }
        frame++;
        animFrameId = requestAnimationFrame(drawGrain);
    };

    window.addEventListener("resize", onResize, { passive: true });
    onResize();
    drawGrain();
}

/* ===================================================================
   3. NAVBAR & SCROLL PROGRESS
   =================================================================== */
function initNavbar() {
    const isEditor = isEditorMode();

    if (!isEditor) {
        document.body.classList.add("js-enabled");
    }

    const navbar = document.querySelector("#top");
    const progress = document.querySelector("#scrollProgress");
    const toTop = document.querySelector("#toTop");
    const hamburger = document.querySelector("#hamburger");
    const navMenu = document.querySelector("#navMenu");
    const navBackdrop = document.querySelector("#navBackdrop");
    const navbarEl = navbar;
    const yearEl = document.querySelector("#year");

    if (yearEl) yearEl.textContent = new Date().getFullYear();

    const onScroll = () => {
        const y = window.scrollY;
        const docH = document.documentElement.scrollHeight - window.innerHeight;
        if (navbar) navbar.classList.toggle("is-scrolled", y > 50);
        if (progress) progress.style.width = (docH > 0 ? (y / docH) * 100 : 0) + "%";
        if (toTop) toTop.classList.toggle("is-visible", y > 700);
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (toTop) {
        toTop.addEventListener("click", () => {
            window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" });
        });
    }

    const closeMenu = () => {
        if (!navMenu) return;
        navMenu.classList.remove("is-open");
        if (hamburger) {
            hamburger.classList.remove("is-open");
            hamburger.setAttribute("aria-expanded", "false");
            hamburger.setAttribute("aria-label", "Open menu");
        }
        document.body.style.overflow = "";
        if (navbarEl) navbarEl.classList.remove("menu-is-open");
        if (navBackdrop) navBackdrop.classList.remove("is-open");
    };

    if (hamburger) {
        hamburger.addEventListener("click", () => {
            if (!navMenu) return;
            const open = navMenu.classList.toggle("is-open");
            hamburger.classList.toggle("is-open", open);
            hamburger.setAttribute("aria-expanded", String(open));
            hamburger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
            document.body.style.overflow = open ? "hidden" : "";
            if (navbarEl) navbarEl.classList.toggle("menu-is-open", open);
            if (navBackdrop) navBackdrop.classList.toggle("is-open", open);
        });
    }

    if (navBackdrop) navBackdrop.addEventListener("click", closeMenu);

    document.querySelectorAll(".nav__link:not(.dropdown-toggle), .nav__cta").forEach(link => {
        link.addEventListener("click", closeMenu);
    });

    document.addEventListener("keydown", ev => {
        if (ev.key === "Escape") closeMenu();
    });

    // Smooth scroll for anchor links
    if (!isEditor) {
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener("click", ev => {
                if (link.getAttribute("data-bs-toggle") || link.classList.contains("dropdown-toggle")) return;
                const id = link.getAttribute("href");
                if (!id || id.length < 2) return;
                const target = document.querySelector(id);
                if (!target) return;
                ev.preventDefault();
                closeMenu();
                const offset = (navbar ? navbar.offsetHeight : 0) + 12;
                window.scrollTo({
                    top: target.getBoundingClientRect().top + window.scrollY - offset,
                    behavior: prefersReduced ? "auto" : "smooth"
                });
            });
        });
    }

    // Scroll reveal observer
    const makeAllVisible = () => {
        document.querySelectorAll(".reveal").forEach(el => el.classList.add("is-visible"));
    };

    if (isEditor) {
        makeAllVisible();
    } else if ("IntersectionObserver" in window && !prefersReduced) {
        const io = new IntersectionObserver(entries => {
            entries.forEach(en => {
                if (en.isIntersecting) {
                    en.target.classList.add("is-visible");
                    io.unobserve(en.target);
                }
            });
        }, { threshold: 0.05, rootMargin: "0px 0px -4% 0px" });
        document.querySelectorAll(".reveal").forEach(el => io.observe(el));

        // Also observe newly inserted snippets dynamically
        const mo = new MutationObserver(mutations => {
            const inEditMode = document.body.classList.contains("editor_enable") || 
                               document.body.classList.contains("editor_has_snippets") ||
                               !!document.querySelector(".editor_enable");
            mutations.forEach(m => {
                m.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        if (inEditMode) {
                            if (node.classList && node.classList.contains("reveal")) {
                                node.classList.add("is-visible");
                            }
                            if (node.querySelectorAll) {
                                node.querySelectorAll(".reveal").forEach(el => el.classList.add("is-visible"));
                            }
                        } else {
                            if (node.classList && node.classList.contains("reveal")) {
                                io.observe(node);
                            }
                            if (node.querySelectorAll) {
                                node.querySelectorAll(".reveal").forEach(el => io.observe(el));
                            }
                        }
                    }
                });
            });
        });
        mo.observe(document.body, { childList: true, subtree: true });
    } else {
        makeAllVisible();
    }

    // Highlight active nav
    const page = window.location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".nav__link").forEach(l => {
        const href = l.getAttribute("href");
        const isHome = (page === "" || page === "index.html") && (href === "index.html" || href === "/" || href === "./");
        l.classList.toggle("is-active", href === page || isHome);
    });
}

/* ===================================================================
   4. HERO BEAM CURSOR
   =================================================================== */
function initHeroBeam() {
    const hero = document.querySelector("#hero");
    if (!hero || prefersReduced) return;

    let tx = window.innerWidth * 0.38;
    let ty = window.innerHeight * 0.58;
    let cx = tx;
    let cy = ty;
    const LERP = 0.07;

    const onMouseMove = e => {
        const r = hero.getBoundingClientRect();
        tx = e.clientX - r.left;
        ty = e.clientY - r.top;
    };

    const animate = () => {
        cx += (tx - cx) * LERP;
        cy += (ty - cy) * LERP;
        hero.style.setProperty("--cx", cx + "px");
        hero.style.setProperty("--cy", cy + "px");
        requestAnimationFrame(animate);
    };

    hero.addEventListener("mousemove", onMouseMove);
    animate();
}

/* ===================================================================
   5. FILM STRIP CAROUSEL
   =================================================================== */
function initFilmStrip() {
    if (isEditorMode()) return;
    const strip = document.querySelector("#filmStrip");
    if (!strip) return;

    const outer = strip.closest(".strip-outer") || strip.parentElement;
    const prevBtn = document.querySelector("#stripPrev");
    const nextBtn = document.querySelector("#stripNext");
    const cards = Array.from(strip.querySelectorAll(".film-card"));
    if (!cards.length) return;

    const DELAY = 3500;
    let current = 0;
    let paused = false;
    let timer = null;

    const dotsEl = document.createElement("div");
    dotsEl.className = "strip-dots";
    const barEl = document.createElement("div");
    barEl.className = "strip-progress-bar";
    const fill = document.createElement("div");
    fill.className = "strip-progress-bar__fill";
    barEl.appendChild(fill);
    outer.insertAdjacentElement("afterend", dotsEl);
    dotsEl.insertAdjacentElement("afterend", barEl);

    const getVisible = () => window.innerWidth >= 1025 ? 4 : window.innerWidth >= 600 ? 2 : 1;
    const getMax = () => Math.max(0, cards.length - getVisible());

    const buildDots = () => {
        dotsEl.innerHTML = "";
        return Array.from({ length: getMax() + 1 }, (_, i) => {
            const d = document.createElement("button");
            d.className = "strip-dot" + (i === current ? " is-active" : "");
            d.setAttribute("aria-label", "Slide " + (i + 1));
            d.addEventListener("click", () => { goTo(i); restartTimer(); });
            dotsEl.appendChild(d);
            return d;
        });
    };

    let dots = buildDots();

    const goTo = idx => {
        current = Math.max(0, Math.min(idx, getMax()));
        const gap = parseInt(getComputedStyle(strip).gap) || 18;
        const cardW = cards[0].offsetWidth;
        strip.style.transform = `translateX(-${current * (cardW + gap)}px)`;
        dots.forEach((d, i) => d.classList.toggle("is-active", i === current));
        if (prevBtn) prevBtn.disabled = current === 0;
        if (nextBtn) nextBtn.disabled = current >= getMax();
        fill.classList.remove("is-running");
        void fill.offsetWidth;
        if (!paused) fill.classList.add("is-running");
    };

    const startTimer = () => {
        timer = setInterval(() => {
            if (!paused) goTo(current >= getMax() ? 0 : current + 1);
        }, DELAY);
    };

    const stopTimer = () => {
        if (timer) clearInterval(timer);
    };

    const restartTimer = () => {
        stopTimer();
        startTimer();
    };

    const runBar = () => {
        fill.classList.remove("is-running");
        void fill.offsetWidth;
        fill.classList.add("is-running");
    };

    if (prevBtn) prevBtn.addEventListener("click", () => { goTo(current - 1); restartTimer(); });
    if (nextBtn) nextBtn.addEventListener("click", () => { goTo(current + 1); restartTimer(); });

    outer.addEventListener("mouseenter", () => {
        paused = true;
        fill.classList.remove("is-running");
    });
    outer.addEventListener("mouseleave", () => {
        paused = false;
        runBar();
    });

    let touchX = 0;
    outer.addEventListener("touchstart", e => { touchX = e.touches[0].clientX; }, { passive: true });
    outer.addEventListener("touchend", e => {
        const dx = e.changedTouches[0].clientX - touchX;
        if (Math.abs(dx) > 40) {
            goTo(current + (dx < 0 ? 1 : -1));
            restartTimer();
        }
    });

    let rzTimer;
    window.addEventListener("resize", () => {
        clearTimeout(rzTimer);
        rzTimer = setTimeout(() => {
            dots = buildDots();
            goTo(Math.min(current, getMax()));
        }, 220);
    });

    goTo(0);
    runBar();
    startTimer();
}

/* ===================================================================
   6. BUTTON RIPPLE
   =================================================================== */
function initRipple() {
    document.querySelectorAll(".btn--ripple").forEach(btn => {
        btn.addEventListener("click", e => {
            const rect = btn.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const r = document.createElement("span");
            r.className = "ripple";
            r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left - size / 2}px;top:${e.clientY - rect.top - size / 2}px`;
            btn.appendChild(r);
            setTimeout(() => r.remove(), 600);
        });
    });
}

/* ===================================================================
   7. SHOWTIME SLOTS & DATE TABS
   =================================================================== */
function initShowtimeSlots() {
    document.querySelectorAll(".board__row").forEach(row => {
        row.querySelectorAll(".time-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                row.querySelectorAll(".time-btn").forEach(b => b.classList.remove("time-btn--lit"));
                btn.classList.add("time-btn--lit");
            });
        });
    });

    document.querySelectorAll(".date-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".date-tab").forEach(t => t.classList.remove("is-active"));
            tab.classList.add("is-active");
        });
    });
}

/* ===================================================================
   8. VIP TICKET 3D TILT & QR
   =================================================================== */
function initTicket3D() {
    const memberTicket = document.querySelector("#memberTicket");
    if (memberTicket) {
        memberTicket.addEventListener("mousemove", e => {
            if (prefersReduced || !window.matchMedia("(pointer:fine)").matches) return;
            const r = memberTicket.getBoundingClientRect();
            const px = (e.clientX - r.left) / r.width - 0.5;
            const py = (e.clientY - r.top) / r.height - 0.5;
            memberTicket.style.transform = `perspective(900px) rotateY(${px * 10}deg) rotateX(${-py * 8}deg)`;
        });

        memberTicket.addEventListener("mouseleave", () => {
            memberTicket.style.transform = "";
        });
    }

    const qr = document.querySelector("#ticketQR");
    if (qr) {
        const ctx = qr.getContext("2d");
        if (ctx) {
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
        }
    }
}

/* ===================================================================
   9. GALLERY LIGHTBOX
   =================================================================== */
function initLightbox() {
    const lb = document.querySelector("#lightbox");
    if (!lb) return;

    const lbImg = lb.querySelector("#lbImg");
    const lbCap = lb.querySelector("#lbCaption");
    const galItems = Array.from(document.querySelectorAll(".gal-item:not([aria-hidden])"));
    if (!galItems.length) return;

    const srcs = galItems.map(f => f.dataset.full || (f.querySelector("img") ? f.querySelector("img").src : ""));
    const caps = galItems.map(f => f.dataset.caption || "");
    let cur = 0;

    const lbShow = i => {
        cur = (i + srcs.length) % srcs.length;
        if (lbImg) {
            lbImg.src = srcs[cur];
            lbImg.alt = caps[cur];
        }
        if (lbCap) lbCap.textContent = caps[cur];
    };

    const lbOpen = i => {
        lbShow(i);
        lb.classList.add("is-open");
        lb.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    };

    const lbClose = () => {
        lb.classList.remove("is-open");
        lb.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    };

    galItems.forEach((f, i) => f.addEventListener("click", () => lbOpen(i)));

    const closeBtn = lb.querySelector("#lbClose");
    if (closeBtn) closeBtn.addEventListener("click", lbClose);

    const prevBtn = lb.querySelector("#lbPrev");
    if (prevBtn) prevBtn.addEventListener("click", () => lbShow(cur - 1));

    const nextBtn = lb.querySelector("#lbNext");
    if (nextBtn) nextBtn.addEventListener("click", () => lbShow(cur + 1));

    lb.addEventListener("click", e => {
        if (e.target === lb) lbClose();
    });

    document.addEventListener("keydown", e => {
        if (!lb.classList.contains("is-open")) return;
        if (e.key === "Escape") lbClose();
        if (e.key === "ArrowRight") lbShow(cur + 1);
        if (e.key === "ArrowLeft") lbShow(cur - 1);
    });
}

/* ===================================================================
   10. TESTIMONIALS CAROUSEL
   =================================================================== */
function initTestimonials() {
    if (isEditorMode()) return;
    const carousel = document.querySelector("#carousel");
    if (!carousel) return;

    const track = carousel.querySelector("#carouselTrack");
    const dotsWrap = carousel.querySelector("#carouselDots");
    if (!track || !dotsWrap) return;

    const slides = Array.from(track.querySelectorAll(".testimonial"));
    if (!slides.length) return;

    let idx = 0;
    let timer = null;

    dotsWrap.innerHTML = "";
    slides.forEach((_, i) => {
        const d = document.createElement("button");
        d.setAttribute("role", "tab");
        d.setAttribute("aria-label", `Testimonial ${i + 1}`);
        if (i === 0) d.classList.add("is-active");
        d.addEventListener("click", () => goTo(i, true));
        dotsWrap.appendChild(d);
    });
    const dots = Array.from(dotsWrap.querySelectorAll("button"));

    const goTo = (i, manual = false) => {
        idx = (i + slides.length) % slides.length;
        track.style.transform = `translateX(-${idx * 100}%)`;
        dots.forEach((d, di) => d.classList.toggle("is-active", di === idx));
        if (manual) restart();
    };

    const start = () => {
        if (!prefersReduced && !timer) {
            timer = setInterval(() => goTo(idx + 1), 5500);
        }
    };

    const stop = () => {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    };

    const restart = () => {
        stop();
        start();
    };

    carousel.addEventListener("mouseenter", stop);
    carousel.addEventListener("mouseleave", start);

    let sx = 0;
    carousel.addEventListener("touchstart", e => { sx = e.touches[0].clientX; stop(); }, { passive: true });
    carousel.addEventListener("touchend", e => {
        const dx = e.changedTouches[0].clientX - sx;
        if (Math.abs(dx) > 50) goTo(idx + (dx < 0 ? 1 : -1), true);
        else start();
    });

    start();
}

/* ===================================================================
   11. TRAILER MODAL
   =================================================================== */
function initTrailerModal() {
    const modal = document.querySelector("#trailerModal");
    const openBtns = document.querySelectorAll("#trailerBtn, .open-trailer-btn");
    if (!modal) return;

    const openModal = () => {
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    };

    const closeModal = () => {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    };

    openBtns.forEach(btn => btn.addEventListener("click", openModal));

    modal.querySelectorAll("[data-close]").forEach(btn => btn.addEventListener("click", closeModal));

    modal.addEventListener("click", e => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener("keydown", e => {
        if (e.key === "Escape" && modal.classList.contains("is-open")) {
            closeModal();
        }
    });
}

/* ===================================================================
   12. BOOKING MODAL
   =================================================================== */
function initBookingModal() {
    const modal = document.querySelector("#bookingModal");
    if (!modal) return;

    const ROWS = "ABCDEFGHIJ".split("");
    const VIP_ROWS = ["A", "B"];
    const COLS = 12;

    const FILMS = {
        "Celestial Drift": { screen: "SCREEN 1 · IMAX", price: 22, vip: 44 },
        "The Velvet Hour": { screen: "SCREEN 2 · PREMIERE", price: 20, vip: 40 },
        "Midnight Sonata": { screen: "SCREEN 3 · DOLBY ATMOS", price: 22, vip: 42 },
        "Golden Empire": { screen: "SCREEN 4 · 4K LASER", price: 20, vip: 40 },
        "The Last Frame": { screen: "SCREEN 5 · DIRECTOR'S CUT", price: 18, vip: 36 }
    };

    const TAKEN = {
        "Celestial Drift": "A3 A8 B2 B7 C4 C10 D1 D6 D11 E5 E9 F3 F8 G2 G7 H5 H11 I4 I9 J3".split(" "),
        "The Velvet Hour": "A1 A6 B4 B9 C2 C7 D5 D10 E3 E8 F1 F6 F11 G4 G9 H2 H7 I5 I10 J8".split(" "),
        "Midnight Sonata": "A2 A9 B5 B11 C3 C8 D4 D9 E1 E7 F5 F10 G3 G8 H1 H6 H12 I3 I8 J6".split(" "),
        "Golden Empire": "A4 A10 B1 B6 C5 C9 D2 D8 E4 E10 F2 F7 G5 G11 H3 H8 I2 I7 J4 J10".split(" "),
        "The Last Frame": "A5 A11 B3 B8 C1 C6 D3 D7 E2 E6 E12 F4 F9 G2 G7 H4 H10 I1 I6 J9".split(" ")
    };

    let selected = [];
    let currentFilm = "";
    let currentTime = "";
    let currentInfo = { screen: "", price: 20, vip: 40 };

    const bSeatList = document.querySelector("#bSeatList");
    const bTotal = document.querySelector("#bTotal");
    const bNext1 = document.querySelector("#bNext1");
    const bDone = document.querySelector("#bDone");
    const bBack2 = document.querySelector("#bBack2");
    const bPay = document.querySelector("#bPay");
    const closeBtn = document.querySelector("#bookingClose");

    const isVipSeat = id => VIP_ROWS.indexOf(id[0]) !== -1;
    const calcTotal = () => selected.reduce((sum, id) => sum + (isVipSeat(id) ? currentInfo.vip : currentInfo.price), 0);

    const updateBar = () => {
        const sorted = selected.slice().sort();
        if (bSeatList) bSeatList.textContent = sorted.length ? sorted.join(", ") : "—";
        if (bTotal) bTotal.textContent = "£" + calcTotal();
        if (bNext1) bNext1.disabled = selected.length === 0;
    };

    const goStep = n => {
        [1, 2, 3].forEach(i => {
            const pane = document.getElementById("bPane" + i);
            const step = modal.querySelector(".bk-step[data-step='" + i + "']");
            if (pane) pane.hidden = (i !== n);
            if (step) {
                step.classList.toggle("is-active", i === n);
                step.classList.toggle("is-done", i < n);
            }
        });
        const panel = modal.querySelector(".booking-modal__panel");
        if (panel) panel.scrollTop = 0;
    };

    const buildSeatMap = () => {
        const map = document.querySelector("#seatMap");
        if (!map) return;
        map.innerHTML = "";
        const wrap = document.createElement("div");
        wrap.className = "seat-rows";
        const takenSet = {};
        (TAKEN[currentFilm] || []).forEach(id => { takenSet[id] = true; });

        ROWS.forEach(row => {
            const rowEl = document.createElement("div");
            rowEl.className = "seat-row";

            const lbl = document.createElement("span");
            lbl.className = "seat-row__lbl";
            lbl.textContent = row;
            rowEl.appendChild(lbl);

            for (let c = 1; c <= COLS; c++) {
                if (c === 7) {
                    const gap = document.createElement("span");
                    gap.className = "seat-row__aisle";
                    rowEl.appendChild(gap);
                }
                const id = row + c;
                const isTaken = !!takenSet[id];
                const isVip = VIP_ROWS.indexOf(row) !== -1;
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
                    seat.addEventListener("click", () => {
                        const idx = selected.indexOf(id);
                        if (idx === -1) {
                            if (selected.length >= 8) return;
                            selected.push(id);
                            seat.classList.add("seat--sel");
                        } else {
                            selected.splice(idx, 1);
                            seat.classList.remove("seat--sel");
                        }
                        updateBar();
                    });
                }
                rowEl.appendChild(seat);
            }
            wrap.appendChild(rowEl);
        });
        map.appendChild(wrap);
    };

    const openModal = (film, time) => {
        currentFilm = film || "Celestial Drift";
        currentTime = time || "19:30";
        currentInfo = FILMS[currentFilm] || { screen: "SCREEN 1 · IMAX", price: 20, vip: 40 };
        selected = [];

        const bFilm = document.querySelector("#bFilm");
        const bScreen = document.querySelector("#bScreen");
        if (bFilm) bFilm.textContent = currentFilm;
        if (bScreen) bScreen.textContent = currentInfo.screen + "  ·  " + currentTime;

        buildSeatMap();
        updateBar();
        goStep(1);

        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    };

    const closeModal = () => {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    };

    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (bDone) bDone.addEventListener("click", closeModal);
    if (bBack2) bBack2.addEventListener("click", () => goStep(1));

    modal.addEventListener("click", e => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener("keydown", e => {
        if (e.key === "Escape" && modal.classList.contains("is-open")) {
            closeModal();
        }
    });

    // Showtime triggers
    document.querySelectorAll(".board__row .time-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const row = btn.closest(".board__row");
            const h3 = row ? row.querySelector("h3") : null;
            const film = h3 ? h3.textContent.trim() : "";
            const time = btn.textContent.trim();
            openModal(film, time);
        });
    });

    document.querySelectorAll(".reserve-btn, .open-booking-modal").forEach(btn => {
        btn.addEventListener("click", ev => {
            ev.preventDefault();
            const film = btn.dataset.film || "Celestial Drift";
            const time = btn.dataset.time || "19:30";
            openModal(film, time);
        });
    });

    if (bNext1) {
        bNext1.addEventListener("click", () => {
            if (!selected.length) return;
            const sorted = selected.slice().sort();
            const std = sorted.filter(id => !isVipSeat(id));
            const vip = sorted.filter(id => isVipSeat(id));
            let html = "";
            if (std.length) html += '<div class="bk-order-row"><span>Standard &times; ' + std.length + '</span><span>&pound;' + (std.length * currentInfo.price) + '</span></div>';
            if (vip.length) html += '<div class="bk-order-row"><span>VIP &times; ' + vip.length + '</span><span>&pound;' + (vip.length * currentInfo.vip) + '</span></div>';
            html += '<div class="bk-order-row"><span>Seats</span><span>' + sorted.join(", ") + '</span></div>';
            html += '<div class="bk-order-row"><span>Showtime</span><span>' + currentTime + '</span></div>';
            html += '<div class="bk-order-row bk-order-row--total"><span>Total</span><span>&pound;' + calcTotal() + '</span></div>';
            const orderBox = document.querySelector("#bOrderBox");
            if (orderBox) orderBox.innerHTML = html;
            goStep(2);
        });
    }

    if (bPay) {
        bPay.addEventListener("click", () => {
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
            const sorted = selected.slice().sort();
            const bTicket = document.querySelector("#bTicket");
            if (bTicket) {
                bTicket.innerHTML =
                    '<div class="bt-ref">' + ref + '</div>' +
                    '<div class="bt-row"><span>FILM</span><span>' + currentFilm + '</span></div>' +
                    '<div class="bt-row"><span>SCREEN</span><span>' + (currentInfo.screen || "") + '</span></div>' +
                    '<div class="bt-row"><span>SHOWTIME</span><span>' + currentTime + '</span></div>' +
                    '<div class="bt-row"><span>SEATS</span><span>' + sorted.join(", ") + '</span></div>' +
                    '<div class="bt-row"><span>GUEST</span><span>' + name + '</span></div>' +
                    '<div class="bt-row"><span>EMAIL</span><span>' + email + '</span></div>' +
                    '<div class="bt-row bt-total"><span>TOTAL PAID</span><span>&pound;' + calcTotal() + '</span></div>';
            }

            const booking = {
                ref: ref,
                film: currentFilm,
                screen: currentInfo.screen || "",
                time: currentTime,
                seats: sorted,
                total: calcTotal(),
                name: name,
                email: email,
                bookedAt: new Date().toISOString()
            };
            const all = JSON.parse(localStorage.getItem("cv_bookings") || "[]");
            all.unshift(booking);
            localStorage.setItem("cv_bookings", JSON.stringify(all));
            window.dispatchEvent(new CustomEvent("cv_booking_updated"));

            goStep(3);
        });
    }

    const cardInput = document.querySelector("#bCard");
    if (cardInput) {
        cardInput.addEventListener("input", () => {
            let v = cardInput.value.replace(/\D/g, "").slice(0, 16);
            cardInput.value = v.replace(/(.{4})/g, "$1 ").trim();
        });
    }

    const expiryInput = document.querySelector("#bExpiry");
    if (expiryInput) {
        expiryInput.addEventListener("input", () => {
            let v = expiryInput.value.replace(/\D/g, "").slice(0, 4);
            if (v.length > 2) v = v.slice(0, 2) + " / " + v.slice(2);
            expiryInput.value = v;
        });
    }
}

/* ===================================================================
   13. BOOKINGS DRAWER
   =================================================================== */
function initBookingsDrawer() {
    const ticketBtn = document.querySelector("#ticketBtn");
    const ticketBadge = document.querySelector("#ticketBadge");
    const drawer = document.querySelector("#bookingsDrawer");
    const drawerClose = document.querySelector("#bookingsClose");
    const drawerBody = document.querySelector("#bookingsBody");
    const drawerBackdrop = document.querySelector("#bookingsBackdrop");

    const renderDrawer = () => {
        const bookings = JSON.parse(localStorage.getItem("cv_bookings") || "[]");
        const count = bookings.length;

        if (ticketBadge && ticketBtn) {
            if (count > 0) {
                ticketBadge.textContent = count > 99 ? "99+" : String(count);
                ticketBadge.hidden = false;
                ticketBtn.classList.add("has-tickets");
            } else {
                ticketBadge.hidden = true;
                ticketBtn.classList.remove("has-tickets");
            }
        }

        if (!drawerBody) return;
        if (count === 0) {
            drawerBody.innerHTML =
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
        drawerBody.innerHTML = html;
    };

    const openDrawer = () => {
        if (!drawer) return;
        renderDrawer();
        drawer.classList.add("is-open");
        drawer.setAttribute("aria-hidden", "false");
        if (ticketBtn) ticketBtn.setAttribute("aria-expanded", "true");
        if (drawerBackdrop) drawerBackdrop.classList.add("is-open");
        document.body.style.overflow = "hidden";
    };

    const closeDrawer = () => {
        if (!drawer) return;
        drawer.classList.remove("is-open");
        drawer.setAttribute("aria-hidden", "true");
        if (ticketBtn) ticketBtn.setAttribute("aria-expanded", "false");
        if (drawerBackdrop) drawerBackdrop.classList.remove("is-open");
        document.body.style.overflow = "";
    };

    if (ticketBtn) {
        ticketBtn.addEventListener("click", () => {
            if (drawer && drawer.classList.contains("is-open")) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });
    }

    if (drawerClose) drawerClose.addEventListener("click", closeDrawer);
    if (drawerBackdrop) drawerBackdrop.addEventListener("click", closeDrawer);

    window.addEventListener("cv_booking_updated", renderDrawer);
    window.addEventListener("storage", ev => {
        if (ev.key === "cv_bookings") renderDrawer();
    });

    document.addEventListener("keydown", e => {
        if (e.key === "Escape" && drawer && drawer.classList.contains("is-open")) {
            closeDrawer();
        }
    });

    renderDrawer();
}
