/** @odoo-module **/

import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";
import { Interaction } from "@web/public/interaction";
import { rpc } from "@web/core/network/rpc";

export class ProductTab extends Interaction {
    static selector = ".product_tab_body";

    async willStart() {
        this.products = await this.waitFor(rpc("/get_product_tab", {}));
    }

    start() {
        if (this.products) {
            this.removeChildren(this.el);
            this.insert(renderToElement("theme_boec.product_tab", { result: this.products }));
        }
    }
}

registry.category("public.interactions").add("theme_boec.product_tab", ProductTab);
