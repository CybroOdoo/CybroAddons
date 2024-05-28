/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from "@web/core/utils/patch";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";

patch(PaymentScreen.prototype, {
    /**
    For payment validation in pos
    **/
    async _finalizeValidation() {
        let customer = this.currentOrder.get_partner();
        if (!customer){
                await this.popup.add(ConfirmPopup, {
                title: _t("Customer Required"),
                body: _t("Customer is required."),
            })
        }
        else{
        jsonrpc('/table/reservation/pos',{
            'partner_id' : customer.id,
            'table_id': this.currentOrder.tableId
        }).then( function(data){})
        return super._finalizeValidation()
    }
    }
});
