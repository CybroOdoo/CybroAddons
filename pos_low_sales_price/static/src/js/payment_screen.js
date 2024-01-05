/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
//Checks whether the sale price greater than cost price each orderlines
patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
                var self = this
                var condition = true
                var flag = true
                var number = 1
                var orderlines = this.pos.selectedOrder.orderlines
                // Checking condition for each orderlines
                orderlines.forEach(async function (lines) {
                     if (lines.product.lst_price < lines.product.standard_price || lines.price < lines.product.standard_price){
                     condition = false
                        const { confirmed } = await self.popup.add(ConfirmPopup,{
                           title:'Alert',
                           body: 'The Sales Price of ' + lines.product.display_name +
                            ' is less than the Cost Price.Do you want to continue validation?',
                           });
                           if (confirmed) {
                           if (orderlines.length==number) {
                          self.pos.showScreen(self.nextScreen)
                           }
                           }
                           }
                           number = number + 1
                })
                if (flag==false && condition== false){
                super.validateOrder(isForceValidate);
                }
                orderlines.forEach(async function (lines) {
                     if ((lines.product.lst_price > lines.product.standard_price || lines.price < lines.product.standard_price)  && condition==true ){
                        self.pos.showScreen(self.nextScreen)
                           }
                })
                }
    });
          export default PaymentScreen;