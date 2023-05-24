odoo.define('theme_lego.index', function(require) {
     "use strict";
    // Import the PublicWidget module
    var PublicWidget = require('web.public.widget');
    // Define a new class named "Slider" that extends the "PublicWidget" class
    var Slider = PublicWidget.Widget.extend({
        // Set the CSS selector for the widget element
        selector: '#slider',
        start: function() {
            var self = this;
            // Call the "onSlider" function to initialize the owlCarousel slider
            self.onSlider();
        },
        // Define the "onSlider" function that initializes the owlCarousel slider
        onSlider: function() {
            var self = this;
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
            // Define a helper function named "counter" that sets the correct slide number for the dots
            function counter() {
                var buttons = self.$el.find('.owl-dots button');
                buttons.each(function(index, item) {
                    $(item).find('span').text(index + 1);
                });
            }
            // Initialize another owlCarousel slider with different options
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
            // Call the "counter" function to set the correct slide number for the dots
            counter();
        }
    });
    // Register the "Slider" class in the PublicWidget registry
    PublicWidget.registry.slider = Slider;
    return Slider;
    });