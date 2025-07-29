/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import { renderToElement } from "@web/core/utils/render";


publicWidget.registry.shopHighlight = animations.Animation.extend({
    selector: ".shop_highlight",

    async willStart() {
        this.$target.empty().html(renderToElement('theme_og_store.shop_highlight_data'))

    },
    start() {
        this._super(...arguments);
        this.shopBanner();
    },


    shopBanner: function() {
        const $slider = this.$('#shop_slide');
            if ($slider.length) {
                $slider.owlCarousel({
                    loop: true,               // Enable infinite loop
                    margin: 40,               // Space between items
                    nav: false,                // Show navigation arrows
                    dots: true,               // Show pagination dots
                    items: 1,
                });
            }
    }
});

export default publicWidget.registry.shopHighlight;
