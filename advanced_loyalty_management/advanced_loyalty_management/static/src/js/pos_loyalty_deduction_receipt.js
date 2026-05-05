/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    export_for_printing() {
    //--------to show the deducted loyalty points details in the order receipt
        const result = super.export_for_printing(...arguments);
        // FIX local: el código original era `this.paymentlines[0].order._isRefundOrder()`,
        // que rompe cuando se imprime/valida una orden sin líneas de pago (caso
        // típico: cambio de mercadería con total $0 sin método elegido). `this`
        // ya es el Order, así que se llama directo. Si por alguna razón no
        // existe el método, se cae a false.
        result.RefundOrder = this._isRefundOrder ? this._isRefundOrder() : false;
        result.pointsDeducted = this.pos.lostPoints
        return result;
    },
});
