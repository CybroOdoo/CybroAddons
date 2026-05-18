/** @odoo-module **/

import animations from "@website/js/content/snippets.animation";
import { rpc } from "@web/core/network/rpc";

animations.registry.get_product_category = animations.Class.extend({
    selector: '.featured_categories',

    onBuilt: function () {
        this.start();
    },
    onClone: function () {
        this.start();
    },
    start: function () {
        this._loadCategories();
    },

    _loadCategories: function () {
        var self = this;

        rpc('/get_product_categories', {})
            .then(function (data) {
                self.$target.empty();
                if (data) {
                    // Append fetched data
                    self.$target.append(data);

                    // Initialize owl carousel after content is loaded
                    self.$('#featured_product').owlCarousel({
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
                            900: { items: 6 }
                        }
                    });
                }
            });
    },
});
