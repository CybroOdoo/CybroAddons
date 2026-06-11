/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },
    async validateOrder(isForceValidate) {
        var order = this.pos.get_order();
        var lines = order.get_orderlines();
        if (this.pos.res_setting['stock_from'] === 'all_warehouse') {
            if (this.pos.res_setting['stock_type'] === 'on_hand') {
                lines.forEach((line) => {
                    var order_quantity = line.qty;
                    var new_qty = line.product_id.qty_available - order_quantity;
                    line.product_id.qty_available = new_qty;
                });
            }else if (this.pos.res_setting['stock_type'] === 'outgoing_qty') {
                lines.forEach((line) => {
                    var order_quantity = line.qty;

                });
            } else if (this.pos.res_setting['stock_type'] === 'incoming_qty') {
                lines.forEach((line) => {
                    var order_quantity = line.qty;
                });
            }
        } else if (this.pos.res_setting['stock_from'] === 'current_warehouse') {
            if (this.pos.res_setting['stock_type'] === 'on_hand') {
                lines.forEach((line) => {
                    var item_quantity = line.qty;
                    var on_hand_qty = line.product_id.qty_available;
                    var new_qty = on_hand_qty - item_quantity;
                    line.product_id.qty_available = new_qty;
                });
            } else if (this.pos.res_setting['stock_type'] === 'outgoing_qty') {
                lines.forEach((line) => {
                    var item_quantity = line.qty;
                    var out_going = line.product_id.outgoing;
                });
            } else if (this.pos.res_setting['stock_type'] === 'incoming_qty') {
                lines.forEach((line) => {
                    var item_quantity = line.qty;
                    var incoming = line.product_id.incoming;
                });
            }
        }
        return super.validateOrder(...arguments);
    }
});
