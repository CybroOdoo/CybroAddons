/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ThemeBuildCraft = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    
    start: function () {
        this._super.apply(this, arguments);
        this._initHamburger();
        this._initNavbarScroll();
        this._initScrollReveal();
        this._initProjectFilter();
        this._initProjectsPageFilter();
        this._initBlogFilter();
        this._initFaqToggle();
        this._initUserDropdown();
    },

    // ... keeping other methods intact, just adding the new one

    _initProjectsPageFilter: function () {
        const tabs = this.el.querySelectorAll('.project-filter-tab');
        const cards = this.el.querySelectorAll('#projects-grid > .project-grid-card');
        const noProjectsMsg = this.el.querySelector('#no-filtered-projects-msg');

        if (tabs.length > 0 && !tabs[0].dataset.initialized) {
            tabs.forEach(tab => {
                tab.dataset.initialized = 'true';
                tab.addEventListener('click', () => {
                    tabs.forEach(t => {
                        t.classList.remove('active', 'bg-primary', 'text-primary-foreground', 'border-primary');
                        t.classList.add('bg-card', 'text-foreground', 'border-border');
                    });
                    tab.classList.add('active', 'bg-primary', 'text-primary-foreground', 'border-primary');
                    tab.classList.remove('bg-card', 'text-foreground', 'border-border');

                    const filter = tab.dataset.filter;
                    let visibleCount = 0;
                    cards.forEach(card => {
                        const match = filter === 'all' || card.dataset.category === filter;
                        card.style.display = match ? '' : 'none';
                        if (match) visibleCount++;
                    });

                    if (noProjectsMsg) {
                        noProjectsMsg.style.display = (visibleCount === 0 && cards.length > 0) ? 'block' : 'none';
                    }
                });
            });
        }
    },

    _initHamburger: function () {
        const menuToggle = document.getElementById('menu-toggle');
        const mobileMenu = document.getElementById('mobile-menu');
        const iconHamburger = document.getElementById('icon-hamburger');
        const iconClose = document.getElementById('icon-close');

        if (menuToggle && !menuToggle.dataset.initialized) {
            menuToggle.dataset.initialized = 'true';
            menuToggle.addEventListener('click', () => {
                const isOpen = mobileMenu.classList.toggle('open');
                iconHamburger.style.display = isOpen ? 'none' : 'block';
                iconClose.style.display = isOpen ? 'block' : 'none';
            });
        }
    },

    _initUserDropdown: function () {
        const userMenuBtn = document.getElementById('bc-avatar-btn');
        const userMenu = document.getElementById('bc-user-menu');

        if (userMenuBtn && userMenu && !userMenuBtn.dataset.initialized) {
            userMenuBtn.dataset.initialized = 'true';
            userMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                userMenu.classList.toggle('open');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!userMenu.contains(e.target)) {
                    userMenu.classList.remove('open');
                }
            });
        }
    },

    _initNavbarScroll: function () {
        const navbar = document.getElementById('navbar');
        if (navbar && !navbar.dataset.scrollInitialized) {
            navbar.dataset.scrollInitialized = 'true';
            window.addEventListener('scroll', () => {
                navbar.classList.toggle('scrolled', window.scrollY > 60);
            }, { passive: true });
        }
    },

    _initScrollReveal: function () {
        // Always re-query elements to catch newly loaded Ajax content
        const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
        if (revealEls.length > 0) {
            const revObserver = new IntersectionObserver((entries) => {
                entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
            }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
            revealEls.forEach(el => revObserver.observe(el));
        }
    },

    _initProjectFilter: function () {
        const filterBtns = document.querySelectorAll('.filter-btn');
        const projectCards = document.querySelectorAll('.project-card');

        if (filterBtns.length > 0 && !filterBtns[0].dataset.initialized) {
            filterBtns.forEach(btn => {
                btn.dataset.initialized = 'true';
                btn.addEventListener('click', () => {
                    const filter = btn.dataset.filter;

                    filterBtns.forEach(b => {
                        b.classList.remove('bg-dark', 'text-white', 'border-dark');
                        b.classList.add('bg-background', 'text-muted-foreground', 'border-border');
                    });
                    btn.classList.remove('bg-background', 'text-muted-foreground', 'border-border');
                    btn.classList.add('bg-dark', 'text-white', 'border-dark');

                    projectCards.forEach(card => {
                        const match = filter === 'all' || card.dataset.category === filter;
                        card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                        if (match) {
                            card.style.opacity = '1';
                            card.style.transform = 'scale(1)';
                            card.style.display = '';
                        } else {
                            card.style.opacity = '0';
                            card.style.transform = 'scale(0.95)';
                            setTimeout(() => {
                                if (card.dataset.category !== filter && filter !== 'all') {
                                    card.style.display = 'none';
                                }
                            }, 300);
                        }
                    });
                });
            });
        }
    },

    _initBlogFilter: function () {
        const tabs = this.el.querySelectorAll('.filter-tab');
        const cards = this.el.querySelectorAll('#articles-grid > .blog-card');

        if (tabs.length > 0 && !tabs[0].dataset.initialized) {
            tabs.forEach(tab => {
                tab.dataset.initialized = 'true';
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    const filter = tab.dataset.filter;

                    cards.forEach(card => {
                        if (filter === 'all' || card.dataset.category === filter) {
                            card.style.display = '';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                });
            });
        }
    },

    _initFaqToggle: function () {
        const faqTriggers = this.el.querySelectorAll('.faq-trigger');
        if (faqTriggers.length > 0 && !faqTriggers[0].dataset.initialized) {
            faqTriggers.forEach(btn => {
                btn.dataset.initialized = 'true';
                btn.addEventListener('click', () => {
                    const body = btn.nextElementSibling;
                    const arrow = btn.querySelector('.faq-arrow');
                    const isOpen = !body.classList.contains('hidden');

                    // Close all
                    this.el.querySelectorAll('.faq-body').forEach(b => b.classList.add('hidden'));
                    this.el.querySelectorAll('.faq-arrow').forEach(a => a.style.transform = '');

                    // Open current if it was closed
                    if (!isOpen) { 
                        body.classList.remove('hidden'); 
                        arrow.style.transform = 'rotate(180deg)'; 
                    }
                });
            });
        }
    }
});

// Since Odoo replaces #wrap but leaves #wrapwrap during soft navigation,
// we also attach a secondary widget specifically to #wrap to ensure
// the reveal logic fires whenever a new page is loaded.
publicWidget.registry.ThemeBuildCraftPage = publicWidget.Widget.extend({
    selector: '#wrap',
    start: function () {
        this._super.apply(this, arguments);
        const revealEls = this.el.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
        if (revealEls.length > 0) {
            const revObserver = new IntersectionObserver((entries) => {
                entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
            }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
            revealEls.forEach(el => revObserver.observe(el));
        }
    }
});