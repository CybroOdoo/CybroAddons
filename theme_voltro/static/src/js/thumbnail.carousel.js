/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";

export const thumbnail_Carousel = PublicWidget.Widget.extend({
    selector: ".homepage",

    // Note: Scroll events on the 'window' are better handled in start()
    // because widgets don't always catch global scroll events in their 'events' map.
    events: {},

    /**
     * @override
     */
    start() {
        const def = this._super.apply(this, arguments);

        // 1. Initialize Carousels (Scoped to this instance)
        this._thumbnail_Carousel();
        this._brandSlider();

        // 2. Setup GSAP ScrollTrigger
        // In Odoo, #wrapwrap is the standard scrolling container.
        // We use this.el.closest('#wrapwrap') to find it safely.
        const scroller = this.el.closest('#wrapwrap') || window;

        // Use scoped selection for the trigger as well
        const rotatingImage = this.el.querySelector(".rotating-image");
        if (rotatingImage) {
            gsap.set(rotatingImage, { rotationY: -180 });
            gsap.to(rotatingImage, {
                scrollTrigger: {
                    trigger: rotatingImage,
                    start: "top center",
                    end: "bottom center",
                    scroller: scroller,
                    scrub: true,
                },
                rotationY: 180,
                ease: "none",
            });
        }

        // 3. Handle Navbar Scroll (Global listener)
        // We attach to window to ensure we catch the scroll even if #wrapwrap isn't used
        window.addEventListener('scroll', this._handleScroll.bind(this));

        return def;
    },

    /**
     * Initialize Splide carousels
     * @private
     */
    _thumbnail_Carousel() {
        const mainEl = this.el.querySelector('#main-carousel');
        const thumbEl = this.el.querySelector('#thumbnail-carousel');

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

            mainCarousel.sync(thumbnailCarousel);
            mainCarousel.mount();
            thumbnailCarousel.mount();
        }
    },

    /**
     * Initialize Owl Carousel for brands
     * @private
     */
    _brandSlider() {
        const $brands = this.$('#brands');
        if ($brands.length) {
            $brands.owlCarousel({
                items: 4,
                loop: true,
                margin: 20,
                autoplay: true,
                autoplayTimeout: 3000,
                autoplayHoverPause: true,
                dots: false,
                nav: false,
                responsive: {
                    0: { items: 1 },
                    600: { items: 2 },
                    1000: { items: 5 }
                }
            });
        }
    },

    /**
     * Handle Navbar styling on scroll
     * @private
     */
    _handleScroll() {
        // Find navbar globally since it's usually outside the .homepage selector
        const navbar = document.getElementById("fixed_nav");
        if (navbar) {
            if (window.pageYOffset > 0) {
                navbar.classList.add("scrolled");
            } else {
                navbar.classList.remove("scrolled");
            }
        }
    },

    /**
     * Clean up listeners when widget is destroyed
     * @override
     */
    destroy() {
        window.removeEventListener('scroll', this._handleScroll);
        this._super.apply(this, arguments);
    },
});

PublicWidget.registry.thumbnail_Carousel = thumbnail_Carousel;