/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class NewArrivalsWidget extends Interaction {
    static selector = ".new_arrivals";

    async willStart() {
        const data = await this.waitFor(rpc("/get_arrival_product", {}));
        this.newArrivals = data.new_arrivals || [];
    }

    start() {
        this.removeChildren(this.el);
        this.renderAt("theme_xtream.s_new_arrivals", { new_arrivals: this.newArrivals });
    }
}

registry.category("public.interactions").add("theme_xtream.new_arrivals", NewArrivalsWidget);
export default NewArrivalsWidget;
