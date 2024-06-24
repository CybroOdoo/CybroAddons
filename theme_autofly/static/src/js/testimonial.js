/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.testimonial = animations.Animation.extend({
    selector: '.testimonial_carousel',
    async start () {
        const data = await jsonrpc('/get_testimonial');
        this.$target.empty().append(renderToElement('theme_autofly.testimonial_snippet', { data, range: this.calculateRange }));
    },
    calculateRange (range) {
       return Array.from({length: range}, (_, index) => index + 1);
    }
})