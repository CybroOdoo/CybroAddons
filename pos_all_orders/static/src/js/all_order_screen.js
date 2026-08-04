/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

class CustomALLOrdrScreen extends Component {
    static template = "pos_all_orders.CustomALLOrdrScreen";
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = useState({
            order: this.props.orders
        });
    }
    back() {
        // on clicking the back button it will redirected Product screen
        this.pos.navigate("ProductScreen");
    }
}
registry.category("pos_pages").add("CustomALLOrdrScreen", {
    name: "CustomALLOrdrScreen",
    component: CustomALLOrdrScreen,
    route: `/pos/ui/${odoo.pos_config_id}/all_orders`,
    params: {},
});
