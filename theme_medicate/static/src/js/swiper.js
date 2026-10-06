/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.Swiper = publicWidget.Widget.extend({
    selector: '.swiper',

    start: function () {
        if (typeof Swiper === 'undefined') {
            return;
        }
        var breakpointsConfig = {
            320: {
                slidesPerView: 1,
                spaceBetween: 10
            },
            768: {
                slidesPerView: 2,
                spaceBetween: 20
            },
            992: {
                slidesPerView: 3,
                spaceBetween: 30
            }
        };

        var swiper1 = new Swiper(".mySwiper-1", {
            slidesPerView: 3,
            spaceBetween: 30,
            breakpoints: breakpointsConfig,
            pagination: {
                el: ".swiper-pagination",
                clickable: true,
            },
        });
        if (window.innerWidth >= 768) {
            var swiper6 = new Swiper(".mySwiper-6", {
                slidesPerView: 3,
                spaceBetween: 30,
                breakpoints: breakpointsConfig,
                pagination: {
                    el: ".swiper-pagination",
                    clickable: true,
                },
            });
        }

        var swiper = new Swiper(".mySwiper-5", {
            slidesPerView: 3,
            spaceBetween: 30,
            breakpoints: breakpointsConfig,
            pagination: {
                el: ".swiper-pagination",
                clickable: true,
            },
        });
        var swiper = new Swiper(".mySwiper-4", {
            slidesPerView: 3,
            spaceBetween: 30,
            freeMode: true,
            breakpoints: breakpointsConfig,
            pagination: {
                el: ".swiper-pagination",
                clickable: true,
            },
        });
    },
});
