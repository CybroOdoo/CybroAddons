/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";


patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.pos = usePos();
    },
    async onAllOrdersClick() {
        const session = this.pos.config.current_session_id.id;
        const configResult = await this.orm.call("pos.session", "get_all_order_config", [], {});
        let orders = [];

        if (configResult.config === "current_session") {
            orders = await this.orm.call("pos.session", "get_all_order", [{ session: session }], {});
        } else if (configResult.config === "past_order") {
            orders = await this.orm.call("pos.session", "get_all_past_orders", [{ session: session }], {});
        } else if (configResult.config === "last_n") {
            orders = await this.orm.call(
                "pos.session",
                "get_all_order",
                [{ session: session, n_days: configResult.n_days }],
                {}
            );
        } else {
            orders = await this.orm.call("pos.session", "get_default_all_orders", [{ session: session }], {});
        }

        this.pos.navigate("CustomALLOrdrScreen", {
            orders: orders,
        });
    },
});