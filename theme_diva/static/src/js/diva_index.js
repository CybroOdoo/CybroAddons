/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.shopCollection = publicWidget.Widget.extend({
    selector: '.shop_collection_class',

    start() {
        return this._super(...arguments).then(() => {
            this._loadShopCollection();
        });
    },

    _loadShopCollection() {
        $.get("/shop_collection_data").then((data) => {
            this.$target.empty().append(data);

            // Initialize the Owl Carousel
            $("#shop_collection_slider").owlCarousel({
                loop: true,
                smartSpeed: 450,
                autoplay: true,
                autoplayTimeout: 1000,
                autoplayHoverPause: true,
                dots: true,
                nav: true,
                navText: [
                    '<i class="bi bi-arrow-left-circle-fill"></i>',
                    '<i class="bi bi-arrow-right-circle-fill"></i>'
                ],
                animateOut: 'fadeOut',
                responsive: {
                    0: { items: 1 },
                    768: { items: 3 },
                },
            });

            // Initialize Animate On Scroll (AOS)
            if (window.AOS) {
                AOS.init({ easing: 'ease-in-quad' });
            }
        });
    },
});

