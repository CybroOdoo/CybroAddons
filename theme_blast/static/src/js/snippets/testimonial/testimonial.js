/** @odoo-module **/

/**
 * Testimonial Widget
 *
 * Loads client testimonials via RPC and initializes
 * an Owl Carousel slider for displaying them.
 *
 * Selector: .testiomnial
 */

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.Testimonial = publicWidget.Widget.extend({
    selector: '.testiomnial',

    async start() {
        const data = await rpc('/get_testimonial', {});
        if (data) {
            this.$target.empty().append(data);
            this.testimonial_slider();
        }
    },

    testimonial_slider(autoplay = false, items = 1, slider_timing = 5000) {
        const self = this;
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
            dots: true,
            nav: true,
            navText: [
                '<i class="fa fa-angle-left" aria-hidden="false"></i>',
                '<i class="fa fa-angle-right" aria-hidden="false"></i>'
            ],
            onInitialized() {
                const buttons = self.$el.find('.owl-dots button');
                buttons.each(function (index, item) {});
            },
        });
    },
});
