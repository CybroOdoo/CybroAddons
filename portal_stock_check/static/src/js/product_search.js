/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class PortalHomeCountersProduct extends Interaction {
    static selector = ".s_website_form";

    dynamicContent = {
        ".o_portal_product_input": {
            "t-on-keyup": this._productSearch,
        },
    };

    async _productSearch(event) {

        const productName = event.currentTarget.value.trim();

        const resultsTable = this.el.querySelector(
            ".product_results_table"
        );

        if (!resultsTable) {
            return;
        }

        try {
            const result = await rpc("/product/search", {
                args: {
                    product: productName,
                },
            });

            resultsTable.replaceChildren(
                renderToElement("productSearch", {
                    result: result,
                })
            );
        } catch (error) {
            resultsTable.replaceChildren();
        }
    }
}

registry.category("public.interactions").add("portal_stock_check.product_search", PortalHomeCountersProduct);