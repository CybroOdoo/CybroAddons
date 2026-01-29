/**
 * Initializes and configures the Owl Carousel for the Diva theme.
 *
 * This module defines the behavior of a carousel using the Owl Carousel library.
 * It sets up the carousel with specific options and handles initialization tasks.
 *
 * @module theme_diva.carousel5
 */
odoo.define('theme_diva.carousel5', function (require) {
    var ajax = require('web.ajax');
    var core = require('web.core');
    var bus = require('web.Bus');
    ajax.loadJS('/path/to/owl.carousel.min.js');
    core.bus.on('DOMContentReady', null, function () {
        var this.$ = core.$;
       // Initialize the Owl Carousel with specified options
        this.$("#owl-carousel").owlCarousel({
            items: 1,
            loop: true,
            margin: 30,
            stagePadding: 30,
            smartSpeed: 450,
            autoplay: false,
            autoPlaySpeed: 1000,
            autoPlayTimeout: 1000,
            autoplayHoverPause: true,
            onInitialized: counter,
            dots: true,
        });
        function counter() {
        }
    });
});
