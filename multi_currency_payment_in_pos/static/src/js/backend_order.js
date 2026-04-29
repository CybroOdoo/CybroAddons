/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";


patch(PosPayment.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);

        if(this.converted_currency){
            result.converted_currency_amount = this.converted_currency.amount
            result.converted_currency_name = this.converted_currency.name
            result.converted_currency_symbol = this.converted_currency.symbol
            this.currency_amount = this.converted_currency.amount
        }

        return result;
    },

});



