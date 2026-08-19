/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { useTrackedAsync } from "@point_of_sale/app/hooks/hooks";

patch(ActionpadWidget.prototype, {

    setup() {
        super.setup(...arguments);
        this.doSubmitOrder = useTrackedAsync(async () => {
            const order = this.pos.getOrder();
            if (!order || order.isEmpty()) {
                return;
            }

            try {
                // Prepare data for server-side kitchen printing
                const orderData = {
                    name: (order.pos_reference && order.pos_reference !== "/") ? order.pos_reference : (order.name && order.name !== "/" ? order.name : order.getName()),
                    pos_config_id: this.pos.config.id,
                    table_name: order.getTable() ? (order.getTable().name || order.getTable().getName()) : "",
                    order_type: order.getTable() ? "Dine In" : (order.preset_id?.name === "Takeout" ? "Take Out" : (order.preset_id?.name || "Take Out")),
                    order_customer_note: order.general_customer_note,
                    order_internal_note: order.internal_note,
                    lines: order.lines.map(line => ({
                        product_id: line.product_id.id,
                        full_product_name: line.getFullProductName(),
                        qty: line.qty,
                        customer_note: line.getCustomerNote(),
                        internal_note: line.getNote(),
                    })),
                };

                // Call server-side print logic BEFORE submitting order
                // This ensures the RPC is sent before navigation/component destruction
                await this.pos.data.call(
                    "pos.order",
                    "print_kitchen_order",
                    [orderData]
                );
            } catch (error) {
                console.error("Kitchen printing failed", error);
            }

            // Standard Odoo POS Order Submission (triggers navigation in pos_restaurant)
            await this.pos.submitOrder();
        });
    },

});
