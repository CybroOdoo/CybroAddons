    /** @odoo-module **/

    /**
     * Public widgets for the University theme.
     *
     * Provides front-end behaviour for the theme's website pages, including the
     * sticky header, back-to-top button, animated statistic counters, scroll
     * reveal animations and the academic programs filter.
     */

    import publicWidget from "@web/legacy/js/public/public_widget";

    /**
     * Widget for handling scrolling and size adjustment effects on the main header navbar.
     */
    publicWidget.registry.UniversityHeader = publicWidget.Widget.extend({
        selector: '#mainNavbar',

        /**
         * @override
         */
        start: function () {
            this._onScroll = this._onScroll.bind(this);
            window.addEventListener('scroll', this._onScroll, { passive: true });
            this._onScroll();

            this._adjustHeaderHeight = this._adjustHeaderHeight.bind(this);
            this._adjustHeaderHeight();

            window.addEventListener('resize', this._adjustHeaderHeight);
            window.addEventListener('load', this._adjustHeaderHeight);

            return this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        destroy: function () {
            window.removeEventListener('scroll', this._onScroll);
            window.removeEventListener('resize', this._adjustHeaderHeight);
            window.removeEventListener('load', this._adjustHeaderHeight);
            this._super.apply(this, arguments);
        },

        /**
         * Toggle the scrolled class on navbar depending on scroll height.
         * @private
         */
        _onScroll: function () {
            this.el.classList.toggle('scrolled', window.scrollY > 60);
        },

        /**
         * Set CSS custom property with header element height.
         * @private
         */
        _adjustHeaderHeight: function () {
            const header = this.el.closest('.site-header');
            if (header) {
                const height = header.offsetHeight;
                document.documentElement.style.setProperty('--header-height', height + 'px');
            }
        }
    });

    /**
     * Widget to manage the back to top smooth-scrolling button visibility and actions.
     */
    publicWidget.registry.UniversityBackToTop = publicWidget.Widget.extend({
        selector: '#backToTop',

        events: {
            'click': '_onClick',
        },

        /**
         * @override
         */
        start: function () {
            this._onScroll = this._onScroll.bind(this);
            window.addEventListener('scroll', this._onScroll, { passive: true });
            this._onScroll();
            return this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        destroy: function () {
            window.removeEventListener('scroll', this._onScroll);
            this._super.apply(this, arguments);
        },

        /**
         * Toggles the visibility of the back-to-top button depending on scroll height.
         * @private
         */
        _onScroll: function () {
            this.el.classList.toggle('visible', window.scrollY > 500);
        },

        /**
         * Smoothly scroll page back to top when clicked.
         * @private
         * @param {Event} e
         */
        _onClick: function (e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    /**
     * Widget for animating statistics count values with custom ease easing functions.
     */
    publicWidget.registry.UniversityCounters = publicWidget.Widget.extend({
        selector: '.stats-section, .hero-stats-row',

        /**
         * @override
         */
        start: function () {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this._animateAll();
                        this.observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.3 });
            this.observer.observe(this.el);
            return this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        destroy: function () {
            if (this.observer) {
                this.observer.disconnect();
            }
            this._super.apply(this, arguments);
        },

        /**
         * Triggers count-up animations for all stat-num nodes.
         * @private
         */
        _animateAll: function () {
            const els = this.el.querySelectorAll('.stat-num');
            els.forEach(el => {
                const raw = el.textContent.trim();
                const targetVal = parseInt(raw.replace(/[^0-9]/g, ''));
                const suffix = raw.replace(/[0-9,]/g, '');
                if (isNaN(targetVal)) return;

                const duration = 1600;
                const start = performance.now();

                function step(now) {
                    const progress = Math.min((now - start) / duration, 1);
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const current = Math.floor(eased * targetVal);
                    el.textContent = current.toLocaleString() + suffix;
                    if (progress < 1) {
                        requestAnimationFrame(step);
                    }
                }
                requestAnimationFrame(step);
            });
        }
    });

    /**
     * Widget to manage lazy element reveal entrance fade-in animations on scroll.
     */
    publicWidget.registry.UniversityReveal = publicWidget.Widget.extend({
        selector: '.reveal',

        /**
         * @override
         */
        start: function () {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');
                        this.observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1, rootMargin: '0px 0px -20px 0px' });
            this.observer.observe(this.el);
            return this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        destroy: function () {
            if (this.observer) {
                this.observer.disconnect();
            }
            this._super.apply(this, arguments);
        }
    });

    /**
     * Widget for handling tab-based filtering of programs inside academics sections.
     */
    publicWidget.registry.UniversityProgramsFilter = publicWidget.Widget.extend({
        selector: '#programs',

        events: {
            'click #programFilterTabs .nav-link': '_onTabClick',
        },

        /**
         * @override
         */
        start: function () {
            this.tabs = this.el.querySelectorAll('#programFilterTabs .nav-link');
            this.grid = this.el.querySelector('#programGrid');
            this.countEl = this.el.querySelector('#programCount');
            this.emptyEl = this.el.querySelector('#programEmpty');
            return this._super.apply(this, arguments);
        },

        /**
         * Event handler triggered when a filter tab is clicked.
         * @private
         * @param {Event} ev
         */
        _onTabClick: function (ev) {
            ev.preventDefault();
            const tab = ev.currentTarget;
            this.tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const filter = tab.dataset.filter;
            const items = this.grid.querySelectorAll('.program-item');

            items.forEach(item => {
                const cat = item.dataset.category;
                if (filter !== 'all' && cat !== filter) {
                    item.classList.add('hiding');
                }
            });

            setTimeout(() => {
                let visible = 0;
                items.forEach(item => {
                    const cat = item.dataset.category;
                    const show = filter === 'all' || cat === filter;
                    if (show) {
                        item.classList.remove('hiding', 'hidden');
                        visible++;
                    } else {
                        item.classList.add('hidden');
                        item.classList.remove('hiding');
                    }
                });
                if (this.countEl) {
                    this.countEl.textContent = visible;
                }
                if (this.emptyEl) {
                    this.emptyEl.classList.toggle('d-none', visible > 0);
                }
            }, 320);
        }
    });
