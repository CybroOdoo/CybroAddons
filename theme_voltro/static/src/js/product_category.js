/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.get_product_category = publicWidget.Widget.extend({
    selector: '.featured_categories',

    start() {
        this._loadCategories();
        return this._super(...arguments);
    },

    _loadCategories() {
        rpc('/get_product_categories').then(data => {
            if (!data) return;

            this.$el.empty().append(data);

            const $carousel = this.$('#featured_product');

            // Prevent double init
            if ($carousel.hasClass('owl-loaded')) {
                $carousel.trigger('destroy.owl.carousel');
            }

            $carousel.owlCarousel({
                loop: true,
                margin: 20,
                nav: false,
                dots: true,
                autoplay: true,
                autoplayTimeout: 5000,
                autoplayHoverPause: true,
                responsive: {
                    0: { items: 1 },
                    400: { items: 2 },
                    600: { items: 3 },
                    800: { items: 4 },
                    900: { items: 6 },
                },
            });
        });
    },
});
