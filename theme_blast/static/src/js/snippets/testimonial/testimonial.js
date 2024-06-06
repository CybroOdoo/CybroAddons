/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
publicWidget.registry.Testimonial = animations.Animation.extend({
    // To extend public widget
        selector: '.testiomnial',
        start: async function () {
        // To get data from controller.
        var self = this;
        await jsonrpc('/get_testimonial', {}).then(function(data) {
            if (data) {
                self.$target.empty().append(data);
                self.testimonial_slider();
            }
        })
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
