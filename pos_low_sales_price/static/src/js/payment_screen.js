/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
//Checks whether the sale price greater than cost price each orderlines
patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
                var self = this
                var product_list = [];
                var orderlines = this.pos.selectedOrder.orderlines
                // Checking condition for each orderlines
                for (const line of orderlines) {
                    if (line.product.lst_price < line.product.standard_price || line.price < line.product.standard_price) {
                        product_list.push("'" + line.product.display_name + "'");
                    }
                }

                if (product_list.length > 0) {
                    var content = '';

                    if (product_list.length === 1) {
                        content = 'The Sales Price of ' + product_list.join(' ') +
                            ' is less than the Cost Price. Do you want to continue validation?';
                    } else {
                        var lastIndex = product_list.length - 1;
                        product_list[lastIndex] = "and " + product_list[lastIndex];
                        content = 'The Sales Prices of ' + product_list.join(', ') +
                            ' are less than the Cost Price. Do you want to continue validation?';
                    }

                    const { confirmed } = await self.popup.add(ConfirmPopup,{
                           title:'Alert',
                           body: content,
                           });

                    if (confirmed) {
                        super.validateOrder(isForceValidate);
                    }
                } else {
                    super.validateOrder(isForceValidate);
                }


                }
    });
          export default PaymentScreen;