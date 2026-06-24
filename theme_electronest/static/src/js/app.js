/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ElectronestHeroSlider = publicWidget.Widget.extend({
    selector: '.heroswiper',
    start: function () {
        this._super.apply(this, arguments);
        if (typeof Swiper !== 'undefined') {
            new Swiper(this.el, {
                autoplay: {
                    delay: 2500,
                    disableOnInteraction: false,
                },
                spaceBetween: 10,
                loop: true,
                speed: 1000,
                pagination: {
                    el: ".swiper-pagination",
                    clickable: true,
                },
            });
        }
    },
});

publicWidget.registry.ElectronestAddSlider = publicWidget.Widget.extend({
    selector: '.addswiper',
    start: function () {
        this._super.apply(this, arguments);
        if (typeof Swiper !== 'undefined') {
            new Swiper(this.el, {
                autoplay: {
                    delay: 2500,
                    disableOnInteraction: false,
                },
                spaceBetween: 10,
                loop: true,
                speed: 1000,
                pagination: {
                    el: ".swiper-pagination",
                    clickable: true,
                },
                navigation: {
                    nextEl: ".swiper-button-next",
                    prevEl: ".swiper-button-prev",
                },
            });
        }
    },
});

publicWidget.registry.ElectronestRecentSlider = publicWidget.Widget.extend({
    selector: '.recentswiper',
    start: function () {
        this._super.apply(this, arguments);
        if (typeof Swiper !== 'undefined') {
            new Swiper(this.el, {
                slidesPerView: 5,
                autoplay: {
                    delay: 2500,
                    disableOnInteraction: false,
                },
                spaceBetween: 10,
                loop: true,
                speed: 1000,
                pagination: {
                    el: ".swiper-pagination",
                    clickable: true,
                },
                navigation: {
                    nextEl: ".swiper-button-next",
                    prevEl: ".swiper-button-prev",
                },
                breakpoints: {
                    0: {
                        slidesPerView: 1,
                    },
                    425: {
                        slidesPerView: 2,
                    },
                    576: {
                        slidesPerView: 2,
                    },
                    768: {
                        slidesPerView: 3,
                    },
                    992: {
                        slidesPerView: 4,
                    },
                    1200: {
                        slidesPerView: 5,
                    },
                },
            });
        }
    },
});

publicWidget.registry.ElectronestCategoryMenu = publicWidget.Widget.extend({
    selector: '.o_electronest_category_menu',

    start: function () {
        this._super.apply(this, arguments);
        this.tabs = Array.from(this.el.querySelectorAll('#mytab .nav-link'));
        this.panes = Array.from(this.el.querySelectorAll('.tab-content .tab-pane'));
        if (!this.tabs.length || !this.panes.length) {
            return;
        }

        this.tabs.forEach((tab) => {
            tab.addEventListener('mouseenter', () => this._activateTab(tab));
            tab.addEventListener('focus', () => this._activateTab(tab));
        });
        this.el.addEventListener('mouseenter', () => this._ensureActiveTab());

        this._ensureActiveTab();
    },

    _ensureActiveTab: function () {
        const activeTab = this.tabs.find((tab) => tab.classList.contains('active'));
        this._activateTab(activeTab || this.tabs[0]);
    },

    _activateTab: function (tab) {
        if (!tab) {
            return;
        }
        const targetSelector = tab.dataset.bsTarget;
        const targetPane = targetSelector && this.el.querySelector(targetSelector);
        if (!targetPane) {
            return;
        }

        this.tabs.forEach((item) => {
            item.classList.remove('active');
            item.setAttribute('aria-selected', 'false');
        });
        this.panes.forEach((pane) => pane.classList.remove('show', 'active'));

        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        targetPane.classList.add('show', 'active');
    },
});
