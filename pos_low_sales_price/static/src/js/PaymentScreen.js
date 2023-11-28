odoo.define('pos_low_sales_price.PaymentScreen', function(require) {
'use strict';
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    /** Created new class validation that extends PaymentScreen and overrides
    the validateOrder **/
    const validation = PaymentScreen => class extends PaymentScreen {
        /**
        Override the function validateOrder to show the warning for sale
        price is less than cost price
        **/
        async validateOrder(isForceValidate) {
            var list_product = []
            var self = this
            var condition = true
            var order_lines = this.env.pos.get_order().orderlines.models
            /** Checking condition for each order_lines **/
            order_lines.forEach(async function (lines) {
                if (lines.product.lst_price < lines.product.standard_price || lines.price < lines.product.standard_price){
                    list_product.push(lines.product.display_name)
                    condition = false
                }
            })
            if(condition == false){
                const { confirmed } = await self.showPopup('ConfirmPopup',{
                title:'Alert',
                body: 'The Sales Price of ' + list_product +
                ' is less than the Cost Price.\nDo you want to continue validation?',
                });
                if (confirmed) {
                    super.validateOrder(...arguments);
                }
            }
            else{
                super.validateOrder(...arguments);
            }
        }
    };
    Registries.Component.extend(PaymentScreen, validation);
    return PaymentScreen;
});
