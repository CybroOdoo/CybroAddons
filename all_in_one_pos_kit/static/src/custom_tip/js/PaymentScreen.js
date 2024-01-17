odoo.define('all_in_one_pos_kit.tips', function (require) {
    'use strict';
    // Extends the PaymentScreen component to add custom methods and properties for tips functionality.
   const Registries = require('point_of_sale.Registries');
   const PaymentScreen = require('point_of_sale.PaymentScreen');
   const { parse } = require('web.field_utils');
    const CustomButtonPaymentScreen = (PaymentScreen) =>class extends PaymentScreen {
       // Overrides the base method to perform additional setup.
       setup() {
           super.setup(...arguments);
       }
        async CustomTipButton(){//Custom method to handle the click event of the custom tip button.
            var custom_tip_percentage = this.env.pos.res_config_settings[this.env.pos.res_config_settings.length-1].custom_tip_percentage
            if(custom_tip_percentage){
                this.env.pos.tips = true;
                this.env.pos.custom_tip = custom_tip_percentage
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
        }
        get Tips() {// Getter method to calculate and provide tip-related information to the template.
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
   };
   // Extend the PaymentScreen component with the custom behavior
   Registries.Component.extend(PaymentScreen, CustomButtonPaymentScreen);
   return CustomButtonPaymentScreen;
});
