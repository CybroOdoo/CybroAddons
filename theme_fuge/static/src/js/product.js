import { registry } from "@web/core/registry";
import { Component, useState, onWillStart} from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

export class FugeProductSnippet extends Component {
    static template = "theme_fuge.product_snippet";
    setup() {
        this.state = useState({ main_products: {}});
        onWillStart(async () => {
            this.currency = await rpc("/website/get_current_currency", { cache: true });
            this.state.main_products = await rpc("/get_main_product", {});
        })
    }
}

registry.category("public_components").add("theme_fuge.FugeProductSnippet", FugeProductSnippet);
