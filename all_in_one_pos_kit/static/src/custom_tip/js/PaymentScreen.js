/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
//import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    onMounted() {
        super.onMounted();
    },
    async CustomTipButton(){
        console.log('kkkkkkkkkkkk')
        //Custom method to handle the click event of the custom tip button.
            var custom_tip_percentage = this.pos.res_config_settings[this.env.pos.res_config_settings.length-1].custom_tip_percentage
            if(custom_tip_percentage){
                this.pos.tips = true;
                this.pos.custom_tip = custom_tip_percentage
                var cust_tip = ((this.currentOrder.get_total_with_tax() + this.currentOrder.get_rounding_applied() ) * parseInt(custom_tip_percentage) /100);
                const { confirmed, payload } = await this.showPopup('NumberPopup', {
                    title: cust_tip ? this.env._t('Change Tip') : this.env._t('Add Tip'),
                    startingValue: cust_tip === 0 && change > 0 ? change : cust_tip,
                    isInputSelected: true,
                });
                if (confirmed) {
                    this.currentOrder.set_tip(parse.float(payload.toString()));
                }
            }
        },
        Tips() {
        // Getter method to calculate and provide tip-related information to the template.
            var custom_tip_percentage = this.env.pos.res_config_settings[this.env.pos.res_config_settings.length-1].custom_tip_percentage
            if(custom_tip_percentage){
                this.env.pos.tips = true;
                this.env.pos.custom_tip = custom_tip_percentage
            }
            else{
                this.env.pos.tips = false;
            }
            return {
                tip:custom_tip_percentage,
                tip_enable:this.env.pos.tips,
            };
        }
    });