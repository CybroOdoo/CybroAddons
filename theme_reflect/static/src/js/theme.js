/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ThemeReflectMain = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    
    events: {
        'click .o_add_wishlist': '_onWishlistClick',
        'click .navbar-toggler': '_onNavbarToggleClick',
        'click .reflect-acc-trigger': '_onAccordionClick',
        'click': '_onAnyClick',
    },

    start() {
        this._initStickyHeader();
        this._initScrollAnimations();
        // Close on outside click
        this.el.ownerDocument.addEventListener('click', (e) => {
            const navCollapse = this.el.querySelector('.navbar-collapse');
            const toggler = this.el.querySelector('.navbar-toggler');
            if (navCollapse && navCollapse.classList.contains('show') &&
                toggler && !toggler.contains(e.target) &&
                !navCollapse.contains(e.target)) {
                navCollapse.classList.remove('show');
                toggler.setAttribute('aria-expanded', 'false');
            }
        });
        // Lock background scroll when mobile sidebar is active
        const mobileMenu = this.el.ownerDocument.querySelector('#reflect_mobile_menu');
        if (mobileMenu) {
            mobileMenu.addEventListener('show.bs.collapse', () => {
                this.el.ownerDocument.documentElement.classList.add('reflect-mobile-menu-open');
                this.el.ownerDocument.body.classList.add('reflect-mobile-menu-open');
            });
            mobileMenu.addEventListener('hide.bs.collapse', () => {
                this.el.ownerDocument.documentElement.classList.remove('reflect-mobile-menu-open');
                this.el.ownerDocument.body.classList.remove('reflect-mobile-menu-open');
            });
        }
        return this._super.apply(this, arguments);
    },

    _onAnyClick(ev) {
        const btn = ev.target.closest('.o_add_wishlist');
        if (!btn) return;
        const icon = btn.querySelector('i');
        if (icon) {
            icon.classList.remove('fa-heart-o', 'text-dark');
            icon.classList.add('fa-heart', 'text-danger');
        }
    },

    _onWishlistClick(e) {
        const w = e.target.closest('.o_add_wishlist');
        if (!w) return;
        const icon = w.querySelector('i');
        if (icon) {
            icon.classList.remove('fa-heart-o', 'text-dark');
            icon.classList.add('fa-heart', 'text-danger');
            w.classList.add('active');
        }
    },

    _initStickyHeader() {
        const header = this.el.querySelector('#top');
        if (!header) return;

        const onScroll = () => {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        };

        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    },

    _onNavbarToggleClick(e) {
        const toggler = e.currentTarget;
        const navCollapse = this.el.querySelector('.navbar-collapse');
        if (!navCollapse) return;
        
        const isOpen = navCollapse.classList.contains('show');
        navCollapse.classList.toggle('show', !isOpen);
        toggler.setAttribute('aria-expanded', String(!isOpen));
    },

    _initScrollAnimations() {
        // Skip in editor mode
        if (this.el.ownerDocument.body.classList.contains('editor_enable')) return;
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

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const siblings = Array.from(
                            entry.target.parentElement?.children || []
                        );
                        const delay = Math.min(siblings.indexOf(entry.target) * 80, 400);
                        setTimeout(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0)';
                        }, delay);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.1, rootMargin: '0px 0px -30px 0px' }
        );

        targets.forEach(el => observer.observe(el));
    },

    _onAccordionClick(e) {
        const trigger = e.currentTarget;
        const item = trigger.closest('.reflect-acc-item');
        if (!item) return;
        const body = item.querySelector('.reflect-acc-body');
        if (!body) return;

        const isOpen = item.classList.contains('open');

        // Close siblings
        const group = item.closest('.reflect-accordion-group');
        if (group) {
            group.querySelectorAll('.reflect-acc-item.open').forEach(open => {
                open.classList.remove('open');
                const openBody = open.querySelector('.reflect-acc-body');
                if (openBody) openBody.style.maxHeight = '0';
            });
        }

        if (!isOpen) {
            item.classList.add('open');
            body.style.maxHeight = body.scrollHeight + 'px';
        }
    }
});
