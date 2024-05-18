/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    /**
    For payment validation in pos
    **/
    async _finalizeValidation() {
        var self = this
        let customer = this.currentOrder.get_partner();
        ajax.jsonRpc('/table/reservation/pos','call',{
            'partner_id' : customer.id,
            'table_id': this.currentOrder.tableId
        }).then( function(data){});
        return super._finalizeValidation()
    }
});
