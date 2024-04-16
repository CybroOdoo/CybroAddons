/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    export_for_printing() {
    //--------to show the deducted loyalty points details in the order receipt
        const result = super.export_for_printing(...arguments);
        result.pointsDeducted = this.pos.lostPoints
        return result;
    },
});
