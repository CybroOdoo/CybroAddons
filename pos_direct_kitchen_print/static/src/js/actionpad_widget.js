/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";

patch(ActionpadWidget.prototype, {

    async submitOrder() {
        const order = this.pos.get_order ? this.pos.get_order() : this.pos.getOrder();
        if (order && !(order.is_empty ? order.is_empty() : order.isEmpty())) {
            try {
                const orderData = {
                    name: (order.pos_reference && order.pos_reference !== "/") ? order.pos_reference : (order.name && order.name !== "/" ? order.name : (order.getName ? order.getName() : order.name)),
                    pos_config_id: this.pos.config.id,
                    table_name: order.getTable ? (order.getTable() ? (order.getTable().name || order.getTable().getName?.() || "") : "") : (order.table ? order.table.name : ""),
                    order_type: order.getTable ? (order.getTable() ? "Dine In" : (order.preset_id?.name === "Takeout" ? "Take Out" : (order.preset_id?.name || "Take Out"))) : "Dine In",
                    order_customer_note: order.general_customer_note || order.customer_note || "",
                    order_internal_note: order.internal_note || "",
                    lines: (order.lines || order.orderlines || []).map(line => ({
                        product_id: line.product_id?.id || line.product?.id || (line.get_product ? line.get_product().id : null),
                        full_product_name: line.getFullProductName ? line.getFullProductName() : (line.get_full_product_name ? line.get_full_product_name() : (line.product_id?.display_name || line.product?.display_name || "")),
                        qty: line.qty !== undefined ? line.qty : (line.get_quantity ? line.get_quantity() : 0),
                        customer_note: line.getCustomerNote ? line.getCustomerNote() : (line.get_customer_note ? line.get_customer_note() : (line.customer_note || "")),
                        internal_note: line.getNote ? line.getNote() : (line.get_note ? line.get_note() : (line.note || "")),
                    })),
                };
                const rpcService = this.pos?.data || this.pos?.orm || this.env?.services?.orm;
                if (!rpcService) {
                    throw new Error("No valid ORM/RPC service found on this.pos or this.env.services");
                }
                await rpcService.call(
                    "pos.order",
                    "print_kitchen_order",
                    [orderData]
                );
            } catch (error) {
                console.error("[pos_direct_kitchen_print] Kitchen printing failed:", error);
            }
        }

        if (super.submitOrder) {
            await super.submitOrder(...arguments);
        }
    },
});
