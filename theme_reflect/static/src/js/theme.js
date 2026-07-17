/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ReflectTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    start() {
        this._initStickyHeader();
        this._initMobileNav();
        this._initScrollAnimations();
        this._initAccordions();
        this._initWishlistVisual();
        return this._super.apply(this, arguments);
    },
    // ── Sticky Header ──────────────────────────────────────────
    _initStickyHeader() {
        const header = this.el.querySelector('#top');
        if (!header) return;

        const onScroll = () => {
            header.classList.toggle('scrolled', window.scrollY > 50);
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    },
    // ── Mobile Nav ─────────────────────────────────────────────
    _initMobileNav() {
        const toggler  = this.el.querySelector('#reflect_mobile_menu_toggler');
        const menu     = this.el.querySelector('#reflect_mobile_menu');
        const closeBtn = this.el.querySelector('#reflect_mobile_menu_close');
        const backdrop = this.el.querySelector('#reflect_mobile_menu_backdrop');

        if (!toggler || !menu) return;

        const openMenu = () => {
            menu.classList.add('is-open');
            toggler.setAttribute('aria-expanded', 'true');
            document.body.style.overflow = 'hidden';
        };

        const closeMenu = () => {
            menu.classList.remove('is-open');
            toggler.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
        };

        toggler.addEventListener('click', openMenu);
        if (closeBtn)  closeBtn.addEventListener('click', closeMenu);
        if (backdrop)  backdrop.addEventListener('click', closeMenu);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && menu.classList.contains('is-open')) {
                closeMenu();
            }
        });
    },
    // ── Scroll-triggered fade-in-up ────────────────────────────
    _initScrollAnimations() {
        if (document.body.classList.contains('editor_enable')) return;
        if (!('IntersectionObserver' in window)) return;

        const targets = this.el.querySelectorAll(
            '.reflect-cat-card, .reflect-product-card, ' +
            '.reflect-feature-card, .reflect-story-card, ' +
            '.reflect-testimonial-card'
        );

        targets.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.55s ease, transform 0.55s ease';
        });

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const siblings = Array.from(entry.target.parentElement?.children || []);
                    const delay = Math.min(siblings.indexOf(entry.target) * 80, 400);
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, delay);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });

        targets.forEach(el => observer.observe(el));
    },
    // ── Accordions ─────────────────────────────────────────────
    _initAccordions() {
        this.el.querySelectorAll('.reflect-acc-trigger').forEach(trigger => {
            trigger.addEventListener('click', function () {
                const item = this.closest('.reflect-acc-item');
                if (!item) return;
                const body = item.querySelector('.reflect-acc-body');
                if (!body) return;

                const isOpen = item.classList.contains('open');

                item.closest('.reflect-accordion-group')
                    ?.querySelectorAll('.reflect-acc-item.open')
                    .forEach(open => {
                        open.classList.remove('open');
                        open.querySelector('.reflect-acc-body').style.maxHeight = '0';
                    });

                if (!isOpen) {
                    item.classList.add('open');
                    body.style.maxHeight = body.scrollHeight + 'px';
                }
            });
        });
    },
    // ── Wishlist Visual Feedback ────────────────────────────────
    _initWishlistVisual() {
        this.el.addEventListener('click', (e) => {
            const wishBtn = e.target.closest('.o_add_wishlist, .o_add_wishlist_dyn');
            if (wishBtn) {
                const icon = wishBtn.querySelector('.fa');
                if (icon) {
                    icon.classList.remove('fa-heart-o', 'text-dark');
                    icon.classList.add('fa-heart', 'text-danger');
                }
            }
        });
    },
});