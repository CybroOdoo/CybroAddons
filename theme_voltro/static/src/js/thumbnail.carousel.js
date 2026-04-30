/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"

export const thumbnail_Carousel = PublicWidget.Widget.extend({
    selector: ".homepage",
    /* Start function for calling slider function */
    events: {
        'scroll': '_handleScroll',
    },
    start() {
        this._thumbnail_Carousel()
        this._brandSlider()
        const actionManager = document.querySelector('.homepage');
        gsap.set(".rotating-image", {rotationY: -180});
        gsap.to(".rotating-image", {
            scrollTrigger: {
                trigger: ".rotating-image",
                start: "top center",
                end: "bottom center",
                scroller: actionManager,
                scrub: true, // Controls the smoothness of the scroll-triggered animation
            },
            rotationY: 180, // Rotates the image 180 degrees
            ease: "none", // Ensures smooth continuous rotation without easing
        });

    },
    /*  Function for about page carousel slider */
    _thumbnail_Carousel() {
        var mainCarousel = new Splide('#main-carousel', {
            type: 'fade',
            rewind: true,
            pagination: false,
            arrows: false,
        });
        // Initialize the thumbnail carousel

        var thumbnailCarousel = new Splide('#thumbnail-carousel', {
            fixedWidth: 100,
            gap: 10,
            rewind: true,
            pagination: false,
            isNavigation: true,
            arrows: false,
        });
        // Synchronize the main carousel with the thumbnails
        mainCarousel.sync(thumbnailCarousel);

        // Mount the carousels
        mainCarousel.mount();
        thumbnailCarousel.mount();

    },


    _brandSlider() {
        this.$('#brands').owlCarousel({
            items: 4,             // Show 4 items at a time
            loop: true,           // Enable continuous loop mode
            margin: 20,           // Space between items
            autoplay: true,       // Enable auto scroll
            autoplayTimeout: 3000, // Time interval for auto scroll (3 seconds)
            autoplayHoverPause: true, // Pause on hover
            dots: false,          // Disable dots
            nav: false,
            responsive: {
                0: {
                    items: 1              // Show 1 item for screen widths 0px and up
                },
                600: {
                    items: 2               // Show 2 items for screen widths 600px and up
                },
                1000: {
                    items: 5                // Show 3 items for screen widths 1000px and up
                }
            }
        });
    },
    _handleScroll() {
        const navbar = document.getElementById("fixed_nav");
        if (window.pageYOffset > 0) {
            navbar.classList.add("scrolled");
        } else {
            navbar.classList.remove("scrolled");
        }

    },

})

PublicWidget.registry.thumbnail_Carousel = thumbnail_Carousel
