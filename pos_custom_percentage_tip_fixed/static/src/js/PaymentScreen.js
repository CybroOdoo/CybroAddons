/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    /**
    load customer tag data to PosGlobalState
    **/
    async _processData(loadedData) {
        await super._processData(loadedData);
        this.res_config = loadedData['res.config.settings'];
    },
});

patch(PaymentScreen.prototype, {
           setup() {
               super.setup(...arguments);
           },
           async CustomTipButton(){
                // It is used to update the tip to payment
                var custom_tip_percentage = this.env.services.pos.res_config[this.env.services.pos.res_config.length-1].custom_tip_percentage
                if(custom_tip_percentage){
                    this.env.services.pos.tips = true;
                    this.env.services.pos.custom_tip = custom_tip_percentage
                    var cust_tip = ((this.currentOrder.get_total_with_tax() + this.currentOrder.get_rounding_applied() ) * parseInt(custom_tip_percentage) /100);
                    let value = cust_tip === 0 && change > 0 ? change : cust_tip;
                    const { confirmed, payload } = await this.popup.add(NumberPopup, {
                        title: cust_tip ? _t("Change Tip") : _t("Add Tip"),
                        startingValue: value,
                        isInputSelected: true,
                        inputSuffix: this.pos.currency.symbol,
                    });
                    if (confirmed) {
                        this.currentOrder.set_tip(parseFloat(payload));
                    }
                    }
           },
           get Tips() {
           // calculates the tips and return to the template
                var custom_tip_percentage = this.env.services.pos.res_config[this.env.services.pos.res_config.length-1].custom_tip_percentage
                if(custom_tip_percentage){
                    this.env.services.pos.tips = true;
                    this.env.services.pos.custom_tip = custom_tip_percentage
                    }
                else{
                    this.env.services.pos.tips = false;
                }
                return {
                        tip:custom_tip_percentage,
                        tip_enable:this.env.services.pos.tips ,
                };
           },
});