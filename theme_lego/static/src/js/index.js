/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.slider = publicWidget.Widget.extend({
    selector: '.owl-carousel',
    start() {
        this.onSlider();
    },

    // Define the "onSlider" function that initializes the owlCarousel slider
    onSlider() {
        this.$el.owlCarousel({
            items: 1,
            loop: true,
            margin: 30,
            stagePadding: 30,
            smartSpeed: 450,
            autoplay: true,
            autoPlaySpeed: 1000,
            autoPlayTimeout: 1000,
            autoplayHoverPause: true,
            dots: true,
            nav: true,
            navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>']
        });
    }
});