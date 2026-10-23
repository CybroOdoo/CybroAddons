/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { OrderDisplay } from "@point_of_sale/app/components/order_display/order_display";

patch(OrderDisplay.prototype, {
    get itemCount() {
        return this.order?.getOrderlines()?.length || 0;
    },

    get totalQuantity() {
        if (!this.order?.getOrderlines()) {
            return 0;
        }
        return this.order.getOrderlines().reduce((total, line) => {
            return total + (line.getQuantity() || 0);
        }, 0);
    }
});
