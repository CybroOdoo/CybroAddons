/** @odoo-module */

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.Exclusive = publicWidget.Widget.extend({
    selector : '.exclusive_categories_section',
    start() {
        this._super(...arguments);
        this._initializeCarousel();
    },

    async willStart() {
        const result = await rpc('/get_exclusive_categories', {});
        if(result){
            this.$target.empty().html(renderToElement('theme_og_store.exclusive_category_data', {result: result}))
        }
    },


    _initializeCarousel() {
        const $slider = this.$('#slider');
        if (!$slider.length) return;

        // Initialize Owl Carousel
        $slider.owlCarousel({
            loop: true,
            margin: 50,
            nav: true,
            dots: false,
            responsive: {
                0: { items: 1 },
                600: { items: 2 },
                1000: { items: 3 }
            }
        });
    },

});

