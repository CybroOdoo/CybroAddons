/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";
import PublicWidget from "@web/legacy/js/public/public_widget";

PublicWidget.registry.trending = PublicWidget.Widget.extend({
    selector: '.trending_snippet_section',

    async start() {
        const result = await rpc('/classic_product_trending', {});

        if (result && result.trending_products) {
            this.$target.html(
                renderToElement(
                    'theme_classic_store.s_classic_store_trending_snippet',
                    { products: result.trending_products }
                )
            );
            // ⬇️ VERY IMPORTANT
            this._initCarousel();
        }
    },

    _initCarousel() {
        const $carousel = this.$el.find('.owl-carousel');

        if (!$carousel.length) {
            return;
        }

        $carousel.owlCarousel({
            margin: 30,
            dots: true,
            nav: true,
            loop: true,
            autoplay: true,
            autoplayTimeout: 5000,
            autoplayHoverPause: true,
            navText: [
                '<i class="fa fa-angle-left"></i>',
                '<i class="fa fa-angle-right"></i>'
            ],
            responsive: {
                0: { items: 1 },
                600: { items: 2 },
                1000: { items: 3 },
            },
        });
    },
});
