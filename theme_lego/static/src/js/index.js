/** @odoo-module **/
// Import the PublicWidget module
import publicWidget from "@web/legacy/js/public/public_widget";
// Define a new class named "Slider" that extends the "PublicWidget" class
publicWidget.registry.slider = publicWidget.Widget.extend({
    // Set the CSS selector for the widget element
    selector: '.owl-carousel',
    start() {
        // Call the "onSlider" function to initialize the owlCarousel slider
        this.onSlider();
    },
    // Define the "onSlider" function that initializes the owlCarousel slider
    onSlider() {
        // Initialize the slider with owlCarousel options
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