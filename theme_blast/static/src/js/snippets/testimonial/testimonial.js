odoo.define('theme_blast.testimonial', function(require) {
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
     //Extending animation class
    Animation.registry.testimonial = Animation.Class.extend({
        selector: '.testiomnial',
        start: function() {
            var self = this;
            ajax.jsonRpc('/get_testimonial', 'call', {})
                .then(function(data) {
                    if (data) {
                        self.$target.empty().append(data);
                        self.testimonial_slider();
                    }
                });
        },
        testimonial_slider: function(autoplay = false, items = 1, slider_timing = 5000) {
            var self = this;
            this.$("#testi").owlCarousel({
                items: 1,
                loop: true,
                margin: 40,
                stagePadding: 30,
                smartSpeed: 450,
                autoplay: true,
                autoPlaySpeed: 1000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,
                onInitialized: counter,
                dots: true,
                nav: true,
                navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
            });

            function counter() {
                var buttons = self.$el.find('.owl-dots button');
                buttons.each(function(index, item) {});
            };
        }
    })
})