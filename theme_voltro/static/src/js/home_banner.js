/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.get_home_banner = publicWidget.Widget.extend({
    selector: '.banner',

    start() {
        this._thumbnailCarousel();
        this._initGsapRotation();
        return this._super(...arguments);
    },

    _initGsapRotation() {
        if (typeof gsap === 'undefined') {
            console.warn('GSAP not loaded');
            return;
        }

        const scroller = document.querySelector('#wrapwrap');

        gsap.set('.rotating-image', { rotationY: -180 });

        gsap.to('.rotating-image', {
            scrollTrigger: {
                trigger: '.rotating-image',
                start: 'top center',
                end: 'bottom center',
                scroller: scroller,
                scrub: true,
            },
            rotationY: 180,
            ease: 'none',
        });
    },

    _thumbnailCarousel() {
        if (typeof Splide === 'undefined') {
            console.warn('Splide not loaded');
            return;
        }

        const mainEl = this.el.querySelector('#main-carousel');
        const thumbEl = this.el.querySelector('#thumbnail-carousel');

        if (!mainEl || !thumbEl) return;

        const mainCarousel = new Splide(mainEl, {
            type: 'fade',
            rewind: true,
            pagination: false,
            arrows: false,
        });

        const thumbnailCarousel = new Splide(thumbEl, {
            fixedWidth: 100,
            gap: 10,
            rewind: true,
            pagination: false,
            isNavigation: true,
            arrows: false,
        });

        mainCarousel.sync(thumbnailCarousel);
        thumbnailCarousel.mount();
        mainCarousel.mount();
    },
});








