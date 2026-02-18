/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.shopHighlight = publicWidget.Widget.extend({
    selector: ".shop_highlight",

    async start() {
        await this._super(...arguments);

        this.el.innerHTML = "";
        this.el.appendChild(
            renderToElement("theme_og_store.shop_highlight_data")
        );

        this.shopBanner();
    },

    shopBanner() {
        const $slider = this.$("#shop_slide");
        if ($slider.length) {
            $slider.owlCarousel({
                loop: true,
                margin: 40,
                nav: false,
                dots: true,
                items: 1,
            });
        }
    },
});

export default publicWidget.registry.shopHighlight;
