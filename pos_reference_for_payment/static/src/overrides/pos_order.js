/** @odoo-module **/

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    set_payment_reference(ref) {
    // Sets the payment reference on the order.
        this.payment_reference = ref;
    },

    get_payment_reference() {
    // Returns the payment reference or an empty string if not set.
        return this.payment_reference || "";
    },

    export_for_printing() {
    // Adds the payment reference to the order data used for printing.
        const data = super.export_for_printing(...arguments);
        data.payment_reference = this.get_payment_reference();
        return data;
    },
});
