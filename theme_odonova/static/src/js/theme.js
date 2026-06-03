/**
 * static/src/js/theme.js
 * ─────────────────────────────────────────────────────────────────────────────
 * OdoNova Theme — frontend JavaScript behaviours.
 *
 * Written as a plain ES module compatible with Odoo 17/18/19's asset pipeline.
 * No jQuery dependency required (Odoo ships it, but we avoid coupling to it
 * for future-proofing).
 *
 * Features:
 *  1. Scroll-aware sticky header  (adds .scrolled class)
 *  2. Intersection Observer scroll-reveal  (.animate-on-scroll → .visible)
 *  3. Animated number counters  (data-target attribute)
 *  4. Mobile navigation toggle
 *  5. Password visibility toggle  (login page)
 *  6. Smooth anchor scrolling
 *  7. Active nav link highlighting based on scroll position
 * ─────────────────────────────────────────────────────────────────────────────
 */

'use strict';


/** ── 1. Scroll-aware header ─────────────────────────────────────────────── */
function initStickyHeader() {
    const header = document.querySelector('[data-odonova-header], .odonova-header');
    if (!header) return;

    const SCROLL_THRESHOLD = 20;

    function onScroll() {
        if (window.scrollY > SCROLL_THRESHOLD) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }

    window.addEventListener('scroll', onScroll, {passive: true});
    onScroll(); // run once on page load
}

/** ── 2. Scroll-reveal via IntersectionObserver ──────────────────────────── */
function initScrollReveal() {
    const targets = document.querySelectorAll('.animate-on-scroll');
    if (!targets.length) return;

    // If browser doesn't support IntersectionObserver, reveal everything immediately
    if (!('IntersectionObserver' in window)) {
        targets.forEach(el => el.classList.add('visible'));
        return;
    }

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    // Unobserve after reveal — no need to watch further
                    observer.unobserve(entry.target);
                }
            });
        },
        {
            threshold: 0.12,    // trigger when 12 % of element is visible
            rootMargin: '0px 0px -40px 0px',
        }
    );

    targets.forEach(el => observer.observe(el));
}

/** ── 3. Animated number counters ────────────────────────────────────────── */
function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    if (isNaN(target)) return;

    const duration = 1800; // ms
    const startTime = performance.now();
    const startValue = 0;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(startValue + (target - startValue) * eased);
        el.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = target;
        }
    }

    requestAnimationFrame(update);
}

function initCounters() {
    const counters = document.querySelectorAll('.odonova-stat-number[data-target]');
    if (!counters.length) return;

    if (!('IntersectionObserver' in window)) {
        counters.forEach(animateCounter);
        return;
    }

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        },
        {threshold: 0.5}
    );

    counters.forEach(el => observer.observe(el));
}

/** ── 4. Mobile navigation toggle ────────────────────────────────────────── */
function initMobileNav() {
    const odooOffcanvas = document.getElementById('top_menu_collapse_mobile');
    if (!odooOffcanvas) return;

    const offcanvasBody = odooOffcanvas.querySelector('.offcanvas-body');
    if (offcanvasBody) {
        offcanvasBody.innerHTML = `
            <ul class="odonova-mobile-nav-list">
                <li><a href="/">Home</a></li>
                <li><a href="/#s_odonova_services">Services</a></li>
                <li><a href="/industries">Industries</a></li>
                <li><a href="/case-studies">Case Studies</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contactus" class="odonova-book-cta">Book Consultation</a></li>
                <li><a href="/web/session/logout" class="odonova-book-cta">Logout</a></li>
            </ul>
        `;
    }

    const offcanvasHeader = odooOffcanvas.querySelector('.offcanvas-header');
    if (offcanvasHeader) offcanvasHeader.style.display = 'none';

    if (!odooOffcanvas.querySelector('.odonova-mobile-logo')) {
        const logoDiv = document.createElement('div');
        logoDiv.className = 'odonova-mobile-logo d-flex align-items-center gap-2 mb-4';
        logoDiv.innerHTML = `
            <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
                <rect width="28" height="28" rx="5" fill="#0b66ff"/>
                <path d="M7 9h5v10H7V9zm9 3h5v7h-5v-7z" fill="#fff"/>
            </svg>
            <span class="odonova-logo-text fs-5 fw-bold">OdoNova</span>
        `;
        odooOffcanvas.insertBefore(logoDiv, odooOffcanvas.firstChild);
    }
}

/** ── 5. Password visibility toggle (login page) ─────────────────────────── */
function initPasswordToggle() {
    document.querySelectorAll('.odonova-pw-toggle, .password-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const wrapper = btn.closest('.odonova-pw-wrap, .password-wrapper');
            if (!wrapper) return;
            const input = wrapper.querySelector('input[type="password"], input[type="text"]');
            if (!input) return;

            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';

            // Swap icon (simple approach — toggle a class)
            btn.classList.toggle('is-visible', isPassword);
            btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
        });
    });
}

/** ── 6. Smooth anchor scrolling ─────────────────────────────────────────── */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href').slice(1);
            if (!targetId) return;
            const target = document.getElementById(targetId);
            if (!target) return;

            e.preventDefault();
            const headerHeight = document.querySelector('.odonova-header, .header')?.offsetHeight || 72;
            const top = target.getBoundingClientRect().top + window.scrollY - headerHeight - 16;

            window.scrollTo({top, behavior: 'smooth'});
        });
    });
}

/** ── 7. Active nav link highlighting ────────────────────────────────────── */
function initActiveNav() {
    const navLinks = document.querySelectorAll('.odonova-navbar .nav-link, .nav a');
    if (!navLinks.length) return;

    const currentPath = window.location.pathname;

    // ── Page-based active: for /industries, /case-studies, /about ──
    // Run immediately — no scroll needed
    navLinks.forEach(link => {
        const href = link.getAttribute('href') || '';
        const linkPath = href.split('#')[0]; // strip any hash

        // Don't match empty paths or bare '/' against sub-pages
        if (linkPath && linkPath !== '/' && currentPath.startsWith(linkPath)) {
            link.classList.add('active');
        }
    });

    // ── Scroll-based active: for anchor links like /#s_odonova_services ──
    // Only relevant on the homepage
    const sections = document.querySelectorAll('section[id]');
    if (!sections.length) return;

    function onScroll() {
        let current = '';
        const headerHeight = document.querySelector('.odonova-header, .header')?.offsetHeight || 72;

        sections.forEach(section => {
            const sectionTop = section.offsetTop - headerHeight - 60;
            if (window.scrollY >= sectionTop) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            // Don't touch links already marked active by the path check above
            const href = link.getAttribute('href') || '';
            const linkPath = href.split('#')[0];
            if (linkPath && linkPath !== '/' && currentPath.startsWith(linkPath)) return;

            link.classList.remove('active');
            if (href === `#${current}` || href.endsWith(`#${current}`)) {
                link.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', onScroll, {passive: true});
    onScroll(); // ← this was the missing call in the original
}

/** ── 8. Form micro-interactions ─────────────────────────────────────────── */
function initFormInteractions() {
    // Floating label effect on consultation / login forms
    document.querySelectorAll('.odonova-form-group input, .odonova-form-group textarea').forEach(input => {
        const label = input.closest('.odonova-form-group')?.querySelector('label');
        if (!label) return;

        function update() {
            label.classList.toggle('has-value', input.value.length > 0);
        }

        input.addEventListener('input', update);
        update();
    });

    // Submit button loading state
    document.querySelectorAll('.odonova-btn-submit, .odonova-btn-login-submit').forEach(btn => {
        btn.closest('form')?.addEventListener('submit', () => {
            btn.disabled = true;
            const original = btn.textContent;
            btn.textContent = 'Sending…';
            // Re-enable after 5s as a safety net (Odoo handles actual submission)
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = original;
            }, 5000);
        });
    });
}

/** ── 9. OdoNova Logo Injection ────────────────────────────────────────────── */
function initOdoNovaLogo() {
    const isOdoNovaTheme = document.querySelector('[data-odonova-header]');
    if (!isOdoNovaTheme) return;

    const logoHTML = `
        <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="5" fill="#0b66ff"/>
            <path d="M7 9h5v10H7V9zm9 3h5v7h-5v-7z" fill="#fff"/>
        </svg>
        <span class="odonova-logo-text fs-5 fw-bold">OdoNova</span>
    `;

    // Target ALL .navbar-brand instances (desktop + mobile)
    document.querySelectorAll('.navbar-brand').forEach(brand => {
        brand.innerHTML = logoHTML;
    });

}

/** ── 10. Hide Contact Us when OdoNova theme is active ─────────────────────── */
function initHideContactUs() {
    const isOdoNovaTheme = document.querySelector('[data-odonova-header]');
    if (!isOdoNovaTheme) return;

    const links = document.querySelectorAll(
        '.navbar a[href="/contactus"]:not(.odonova-book-cta), .nav-item a[href="/contactus"]:not(.odonova-book-cta)');
    links.forEach(link => {
        link.closest('.nav-item')
            ? link.closest('.nav-item').style.display = 'none'
            : link.style.display = 'none';
    });
}

/** ── 11. Smooth scroll for navbar anchor links ───────────────────────────── */
function initNavAnchorScroll() {
    const isOdoNovaTheme = document.querySelector('[data-odonova-header]');
    if (!isOdoNovaTheme) return;

    document.querySelectorAll('.navbar a[href^="#"]').forEach(link => {
        link.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href').substring(1);
            if (!targetId) return;

            // Try id first
            let target = document.getElementById(targetId);

            // Fallback: find by class name
            if (!target) {
                target = document.querySelector(
                    `.${targetId}, [data-snippet="${targetId}"], .s_odonova_${targetId}`
                );
            }

            if (target) {
                e.preventDefault();
                target.scrollIntoView({behavior: 'smooth', block: 'start'});
            }
        });
    });
}

/** ── Init ───────────────────────────────────────────────────────────────── */
function odonovaThemeInit() {
    initStickyHeader();
    initScrollReveal();
    initCounters();
    initMobileNav();
    initPasswordToggle();
    initSmoothScroll();
    initActiveNav();
    initFormInteractions();
    initOdoNovaLogo();
    initHideContactUs()
    initNavAnchorScroll()
}

// Run after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', odonovaThemeInit);
} else {
    odonovaThemeInit();
}

// Also hook into Odoo's SPA router events so the theme re-inits
// after soft navigations (website editor, etc.)
document.addEventListener('odoo.initialized', odonovaThemeInit);

// Export for potential use in other Odoo JS modules
export {odonovaThemeInit};
