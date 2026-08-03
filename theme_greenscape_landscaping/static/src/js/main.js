/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Greenscape Theme Widget
 *
 * This widget manages the interactive frontend behavior of the Greenscape
 * homepage. It initializes the sticky navigation bar, mobile navigation,
 * active menu highlighting, portfolio filtering, smooth scrolling, and
 * toast notifications.
 */
publicWidget.registry.GreenscapeTheme = publicWidget.Widget.extend({
    selector: '.greenscape-home',

    /**
     * Initializes all frontend interactions for the Greenscape theme.
     *
     * @override
     * @returns {Promise} Promise returned by the parent widget.
     */
    start: function () {
        this._initStickyNavbar();
        this._initMobileMenu();
        this._initActiveNavLink();
        this._initPortfolioFilter();
        this._initSmoothScroll();
        return this._super.apply(this, arguments);
    },

    /**
     * Enables the sticky navigation bar effect.
     *
     * Adds the `scrolled` CSS class when the page is scrolled
     * beyond 60 pixels.
     *
     * @private
     */
    _initStickyNavbar: function () {
        const navbar = this.el.querySelector('.navbar');
        const handleScroll = () => {
            navbar?.classList.toggle('scrolled', window.scrollY > 60);
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll();
    },

    /**
     * Initializes the mobile navigation menu.
     *
     * Toggles the mobile menu visibility when the hamburger icon
     * is clicked and automatically closes the menu when a navigation
     * link is selected.
     *
     * @private
     */
    _initMobileMenu: function () {
        const hamburger = this.el.querySelector('.hamburger');
        const navLinks = this.el.querySelector('.nav-links');
        if (hamburger && navLinks) {
            hamburger.addEventListener('click', () => {
                const isOpen = navLinks.classList.toggle('open');
                hamburger.classList.toggle('open');
                hamburger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            });

            navLinks.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    navLinks.classList.remove('open');
                    hamburger.classList.remove('open');
                    hamburger.setAttribute('aria-expanded', 'false');
                });
            });
        }
    },

    /**
     * Highlights the active navigation link based on the
     * current page URL.
     *
     * @private
     */
    _initActiveNavLink: function () {
        const currentPage = window.location.pathname;
        this.el.querySelectorAll('.nav-links a').forEach(link => {
            const href = (link.getAttribute('href') || '').split('#')[0];
            if (href === currentPage || (currentPage === '/' && href === '/')) {
                link.classList.add('active');
            } else if (currentPage !== '/' && href !== '/') {
                link.classList.remove('active');
            }
        });
    },

    /**
     * Initializes portfolio category filtering.
     *
     * Displays only portfolio items matching the selected category.
     * Selecting the "all" filter makes every portfolio item visible.
     *
     * @private
     */
    _initPortfolioFilter: function () {
        const filterBtns = this.el.querySelectorAll('.filter-btn');
        const portfolioItems = this.el.querySelectorAll('.portfolio-item');

        if (filterBtns.length > 0 && portfolioItems.length > 0) {
            filterBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    filterBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    const filter = btn.dataset.filter;
                    portfolioItems.forEach(item => {
                        item.classList.toggle(
                            'hidden',
                            filter !== 'all' && item.dataset.category !== filter
                        );
                    });
                });
            });
        }
    },

    /**
     * Enables smooth scrolling for in-page anchor links.
     *
     * Scrolls smoothly to the target section while compensating
     * for the fixed navigation bar height.
     *
     * @private
     */
    _initSmoothScroll: function () {
        this.el.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                const href = anchor.getAttribute('href');
                if (href !== '#' && href.startsWith('#')) {
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        window.scrollTo({
                            top: target.offsetTop - 80,
                            behavior: 'smooth',
                        });
                    }
                }
            });
        });
    },

    /**
     * Displays a temporary toast notification.
     *
     * @private
     * @param {string} msg Message to display.
     * @param {string} [type='success'] Notification type. Supported values are
     *   `success` and `error`.
     */
    _showNotification: function (msg, type = 'success') {
        const toast = document.createElement('div');
        toast.innerHTML = `<span>${type === 'success' ? '&#10003;' : '!'}</span> ${msg}`;
        toast.style.cssText = `
          position:fixed; bottom:28px; right:28px; z-index:9999;
          background:${type === 'success' ? 'var(--primary)' : '#e53935'};
          color:white; padding:16px 24px; border-radius:12px;
          box-shadow:0 8px 24px rgba(0,0,0,0.2); font-size:0.9rem;
          display:flex; align-items:center; gap:10px;
          max-width:380px; font-family:var(--font-primary);
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
});