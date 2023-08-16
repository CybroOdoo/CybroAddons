odoo.define('pos_low_sales_price.validation', function(require) {
'use strict';
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
// Created new class validation that extends PaymentScreen and overrides the validateOrder
const validation = PaymentScreen =>
    class extends PaymentScreen {
         validateOrder(isForceValidate) {
                var self = this
                var condition = true
                var flag = true
                var number = 1
                var orderlines = this.env.pos.selectedOrder.orderlines
                // Checking condition for each orderlines
                orderlines.forEach(async function (lines) {
                     if (lines.product.lst_price < lines.product.standard_price || lines.price < lines.product.standard_price){
                     condition = false
                        const { confirmed } = await self.showPopup('ConfirmPopup',{
                           title:'Alert',
                           body: 'The Sales Price of ' + lines.product.display_name +
                            ' is less than the Cost Price.Do you want to continue validation?',
                           });
                           if (confirmed) {
                           if (orderlines.length==number) {
                           self.showScreen(self.nextScreen)
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
                     self.showScreen(self.nextScreen)
                           }
                })
                }
        };
        Registries.Component.extend(PaymentScreen, validation);
        return PaymentScreen;
    });