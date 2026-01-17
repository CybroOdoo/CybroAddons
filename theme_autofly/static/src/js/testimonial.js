/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.testimonial = publicWidget.Widget.extend({
    selector: '.testimonial_carousel',
    async start () {
        const data = await rpc('/get_testimonial');
        this.$target.empty().append(renderToElement('theme_autofly.testimonial_snippet', { data, range: this.calculateRange }));
    },
    calculateRange (range) {
       return Array.from({length: range}, (_, index) => index + 1);
    }
})
