/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    export_for_printing() {
    //--------to show the deducted loyalty points details in the order receipt
        const result = super.export_for_printing(...arguments);
        // Validate that payment lines exist before accessing
        if (this.paymentlines && this.paymentlines.length > 0) {
            result.RefundOrder = this.paymentlines[0].order._isRefundOrder();
        } else { result.RefundOrder = false; }
        result.pointsDeducted = this.pos.lostPoints || 0; return result;
         },
    });

