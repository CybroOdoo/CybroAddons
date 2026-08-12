/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { renderToElement } from "@web/core/utils/render";
import { jsonrpc } from "@web/core/network/rpc_service";
import { markup } from "@odoo/owl";

publicWidget.registry.SolarionSolutionsWidget = publicWidget.Widget.extend({
    selector: '.js_solarion_solutions_widget',

    init() {
        this._super(...arguments);
    },

    async start() {
        await this._super(...arguments);
        const data = await jsonrpc('/theme_solarion/get_solutions_data');

        if (data) {
            if (data.featured_product && data.featured_product.description) {
                data.featured_product.description = markup(data.featured_product.description);
            }
            if (data.other_products) {
                data.other_products.forEach((prod) => {
                    if (prod.description) {
                        prod.description = markup(prod.description);
                    }
                });
            }

            const targetEl = this.el.querySelector('.js_solutions_content') || this.el;
            const renderedContent = renderToElement('theme_solarion.solutions_dynamic_content', {
                featured_product: data.featured_product,
                other_products: data.other_products,
            });
            if (renderedContent) {
                targetEl.replaceChildren(renderedContent);
            }
        }
    },
});

export default publicWidget.registry.SolarionSolutionsWidget;
