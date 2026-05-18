/** @odoo-module **/

import animations from "@website/js/content/snippets.animation";

animations.registry.get_home_banner = animations.Class.extend({
    selector: '.banner',

    /**
     * @override
     */
    start: function () {
        const def = this._super.apply(this, arguments);

        // 1. Initialize Carousels
        this._thumbnail_Carousel();

        // 2. Setup GSAP with Odoo-safe scroller
        // this.el.closest('#wrapwrap') finds the main scrolling area relative to this snippet
        const scroller = this.el.closest('#wrapwrap') || window;

        gsap.set(".rotating-image", { rotationY: -180 });
        gsap.to(".rotating-image", {
            scrollTrigger: {
                trigger: this.el.querySelector(".rotating-image"),
                start: "top center",
                end: "bottom center",
                scroller: scroller,
                scrub: true, // Controls the smoothness of the scroll-triggered animation
            },
            rotationY: 180, // Rotates the image 180 degrees
            ease: "none", // Ensures smooth continuous rotation without easing
        });

        return def;
    },

    /**
     * Initialize Splide carousels scoped to this snippet instance
     * @private
     */
    _thumbnail_Carousel: function () {
        const mainEl = this.el.querySelector('#main-carousel');
        const thumbEl = this.el.querySelector('#thumbnail-carousel');

        // Check if elements exist before mounting
        if (mainEl && thumbEl) {
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

            // Synchronize and mount
            mainCarousel.sync(thumbnailCarousel);
            mainCarousel.mount();
            thumbnailCarousel.mount();
        }
    },
});