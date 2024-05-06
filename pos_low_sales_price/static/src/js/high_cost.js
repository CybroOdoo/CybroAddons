odoo.define('pos_low_sales_price.validation', function(require) {
'use strict';
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
// Created new class validation that extends PaymentScreen and overrides the validateOrder
const validation = PaymentScreen =>
    class extends PaymentScreen {
           async validateOrder(isForceValidate) {
                var self = this
                var condition = true
                var flag = true
                var normal_flow = false
                var number = 1
                var orderlines = this.env.pos.selectedOrder.orderlines
                // Checking condition for each orderlines
                for (const lines of orderlines) {
                    if (lines.product.lst_price < lines.product.standard_price || lines.price < lines.product.standard_price) {
                        condition = false;
                        const { confirmed } = await self.showPopup('ConfirmPopup', {
                            title: 'Alert',
                            body: 'The Sales Price of ' + lines.product.display_name +
                                ' is less than the Cost Price. Do you want to continue validation?',
                        });
                        if (confirmed) {
                             // Set flag to false if popup is confirmed
                            if (orderlines.length === number) {
                                flag = false;
                            }
                        }
                    }
                    else{
                    // Set normal_flow to true if there is no pop-up
                    normal_flow = true

                    }
                    number = number + 1
                }


                if (normal_flow == true){
                 // Order validation for normal flow
                super.validateOrder(isForceValidate);
                }
                if (flag==false && condition== false && normal_flow== false){
                // Order validation for low price product after confirming the pop-up
                super.validateOrder(isForceValidate);
                }

           }
        };
        Registries.Component.extend(PaymentScreen, validation);
        return PaymentScreen;
    });