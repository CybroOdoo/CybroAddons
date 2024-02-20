odoo.define('theme_eco_refine.customer_response_snippet', function (require) {
    'use strict';
      /**
     * Customer response carousel.
     */
    var publicWidget = require('web.public.widget');

    publicWidget.registry.eco_customer_response = publicWidget.Widget.extend({
        selector: '.customer_response',  // Update with your actual selector

        start: function () {
            this._initializeOwlCarousel();
            this._bindCustomNavigation();
            return this._super.apply(this, arguments);
        },
        _initializeOwlCarousel: function () {
            this.$('.owl-carousel1').owlCarousel({
                loop: true,
                margin: 10,
                navText: ["Prev", "Next"],
                nav: false,
                autoplay: true,
                responsive: {
                    0: {
                        items: 2
                    },
                    600: {
                        items: 3
                    },
                    1000: {
                        items: 5
                    }
                }
            });
            this.$(".owl-carousel2").owlCarousel({
                items: 1,
                loop: true,
                nav: false,
                dots: false,
                // Add more options as needed
            });
        },
        _bindCustomNavigation: function () {
            var self = this;
            this.$(".custom-nav__prev").click(function () {
                self.$(".owl-carousel2").trigger("prev.owl.carousel");
            });
            this.$(".custom-nav__next").click(function () {
                self.$(".owl-carousel2").trigger("next.owl.carousel");
            });
        },
    });
    return publicWidget.registry.refurb_theme_product;
});
