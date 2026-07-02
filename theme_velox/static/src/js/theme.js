/** @odoo-module **/
/** Client-side animations, search overlay interactions, and responsive navigation header. */

import publicWidget from '@web/legacy/js/public/public_widget';

/* ─────────────────────────────────────────────────────────
   1. Search overlay — wired once, never re-wired
───────────────────────────────────────────────────────── */
(function initSearchOverlay() {
    function wire() {
        const overlay = document.getElementById('searchOverlay');
        if (!overlay) return;

        const openBtn = document.getElementById('openSearchBtn');
        const closeBtn = document.getElementById('closeSearchBtn');
        const input    = document.getElementById('searchInput');

        const open = () => {
            overlay.classList.add('active');
            overlay.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            // Short delay lets the CSS opacity transition start before focus
            if (input) setTimeout(() => input.focus(), 250);
        };

        const close = () => {
            overlay.classList.remove('active');
            overlay.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        };

        if (openBtn)  openBtn.addEventListener('click',  e => { e.preventDefault(); open(); });
        if (closeBtn) closeBtn.addEventListener('click',  close);

        // Click outside the inner content box also closes
        overlay.addEventListener('click', e => {
            if (e.target === overlay) close();
        });

        // Keyboard Escape closes
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && overlay.classList.contains('active')) {
                close();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', wire, { once: true });
    } else {
        wire();
    }
})();


/* ─────────────────────────────────────────────────────────
   2. publicWidget — runs on every page / navigation
───────────────────────────────────────────────────────── */
publicWidget.registry.VeloxTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    /**
     * disabledInEditableMode: false  →  the widget also runs while the
     * website builder is open, so the sticky nav keeps working in edit mode.
     */
    disabledInEditableMode: false,

    start() {
        const sup = this._super(...arguments);
        this._initStickyNav();
        this._initParallax();
        this._initCountUp();
        return sup;
    },

    destroy() {
        // Clean up scroll listeners to prevent memory leaks on navigation
        if (this._onScrollNav)      window.removeEventListener('scroll', this._onScrollNav);
        if (this._onScrollParallax) window.removeEventListener('scroll', this._onScrollParallax);
        this._super(...arguments);
    },

    /* ── Sticky nav shadow ───────────────────────────────── */
    _initStickyNav() {
        const nav = document.querySelector('.velox-nav');
        if (!nav) return;

        this._onScrollNav = () => {
            nav.classList.toggle('velox-nav-scrolled', window.scrollY > 40);
        };
        window.addEventListener('scroll', this._onScrollNav, { passive: true });
        // Run once immediately in case page loads mid-scroll
        this._onScrollNav();
    },

    /* ── Hero parallax (respects prefers-reduced-motion) ─── */
    _initParallax() {
        const hero = document.querySelector('.s_velox_hero');
        if (!hero) return;
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        let ticking = false;
        this._onScrollParallax = () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    if (hero?.style) {
                        hero.style.backgroundPositionY =
                            `calc(50% + ${window.scrollY * 0.25}px)`;
                    }
                    ticking = false;
                });
                ticking = true;
            }
        };
        window.addEventListener('scroll', this._onScrollParallax, { passive: true });
    },

    /* ── Stats count-up animation (IntersectionObserver) ─── */
    _initCountUp() {
        const statEls = this.el.querySelectorAll('.velox-stat-number');
        if (!statEls.length || !('IntersectionObserver' in window)) return;

        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                observer.unobserve(entry.target);

                const el      = entry.target;
                const raw     = el.textContent.trim();         // e.g. "2M+"
                const suffix  = raw.replace(/[\d.]/g, '');     // "M+"
                const target  = parseFloat(raw) || 0;
                const dur     = 1400;                           // ms
                const start   = performance.now();

                const tick = now => {
                    const progress = Math.min((now - start) / dur, 1);
                    // Ease-out cubic
                    const eased   = 1 - Math.pow(1 - progress, 3);
                    const current = Math.round(eased * target);
                    el.textContent = current + suffix;
                    if (progress < 1) requestAnimationFrame(tick);
                };
                requestAnimationFrame(tick);
            });
        }, { threshold: 0.5 });

        statEls.forEach(el => observer.observe(el));
    },
});
