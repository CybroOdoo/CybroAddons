/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.get_home_brands = publicWidget.Widget.extend({
    selector: '.brands',

    start() {
        const $carousel = this.$('#brands');
        if ($carousel.length) {
            // Prevent double init
            if ($carousel.hasClass('owl-loaded')) {
                $carousel.trigger('destroy.owl.carousel');
            }

            $carousel.owlCarousel({
                items: 4,
                loop: true,
                margin: 20,
                autoplay: true,
                autoplayTimeout: 3000,
                autoplayHoverPause: true,
                dots: false,
                nav: false,
                responsive: {
                    0: { items: 1 },
                    600: { items: 2 },
                    1000: { items: 5 },
                },
            });
        }

        return this._super(...arguments);
    },
});
