/** @odoo-module */

import PublicWidget from "@web/legacy/js/public/public_widget"
// Define a new widget called NavigationScroll
export const ThemeVoltro = PublicWidget.Widget.extend({
    // Set the selector to the element with id 'wrapwrap', which is the main wrapper of the page
    selector: "#wrapwrap",
    // Define the events to be handled by the widget
    events: {
        'scroll': '_handleScroll',
    },
    start() {
    },
    _handleScroll() {
    }


});

PublicWidget.registry.ThemeVoltro = ThemeVoltro;


_thumbnail_Carousel()
{
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
        pagination: true,
        isNavigation: true,
        arrows: false,
        breakpoints: {
            600: {
                fixedWidth: 60,
                fixedHeight: 100,
            },
        },
    });
    // Synchronize the main carousel with the thumbnails
    mainCarousel.sync(thumbnailCarousel);

    // Mount the carousels
    mainCarousel.mount();
    thumbnailCarousel.mount();

}

