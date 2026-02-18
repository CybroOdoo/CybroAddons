/** @odoo-module */

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.get_product_tab = publicWidget.Widget.extend({
    selector : '.categories_section',
    async willStart() {
        const result = await rpc('/get_product_categories', {});
        if(result){
            this.$target.empty().html(renderToElement('theme_og_store.category_data', {result: result}))
        }
    },

    start() {
        this._super(...arguments);
        this._initializeCarousel();
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
                1000: { items: 7 }
            }
        });
    },

});