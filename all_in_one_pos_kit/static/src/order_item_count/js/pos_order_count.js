/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

// Item count / total quantity of an order, used by the order summary on the
// product screen and by the receipt.
patch(PosOrder.prototype, {
    get itemCount() {
        return this.lines ? this.lines.length : 0;
    },

    get totalQuantity() {
        return (this.lines || []).reduce(
            (total, line) => total + (parseFloat(line.qty) || 0),
            0
        );
    },
});
