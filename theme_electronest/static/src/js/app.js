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

