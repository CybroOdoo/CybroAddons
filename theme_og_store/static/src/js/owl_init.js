/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.OwlCarouselInit = publicWidget.Widget.extend({
    selector: ".owl-carousel",

    start() {
        if (!this.$el.hasClass("owl-loaded")) {
            this.$el.owlCarousel({
                loop: true,
                margin: 10,
                nav: true,
                responsive: {
                    0: { items: 1 },
                    600: { items: 3 },
                    1000: { items: 5 },
                },
            });
        }
        return this._super(...arguments);
    },
});