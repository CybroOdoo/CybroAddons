odoo.define('membership_in_pos.membership', function (require) {
    'use strict';
   var { PosGlobalState } = require('point_of_sale.models');
   const Registries = require('point_of_sale.Registries');
   const PaymentScreen = require('point_of_sale.PaymentScreen');
   const PosMembershipGlobalState = (PosGlobalState) =>
   class PosMembershipGlobalState extends PosGlobalState {
    //@override
        async _processData(loadedData) {
            await super._processData(loadedData);
            this.res_config = loadedData['res.config.settings'];
        }
    }
    Registries.Model.extend(PosGlobalState, PosMembershipGlobalState);
    //extends the payment screen
    const CustomButtonPaymentScreen = (PaymentScreen) =>
       class extends PaymentScreen {
           setup() {
               super.setup(...arguments);
               this.env.pos.membership = this.env.pos.res_config[this.env.pos.res_config.length-1].is_pos_module_pos_membership
           }
           async MemberShipButton() {
               // click_membership shows the pop up
               const { confirmed } = await this.showPopup('MembershipPopup');
           }
       };
   Registries.Component.extend(PaymentScreen, CustomButtonPaymentScreen);
   return CustomButtonPaymentScreen;
});
