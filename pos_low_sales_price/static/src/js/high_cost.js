odoo.define('pos_low_sales_price.validation', function(require) {
    'use strict';
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    // Created new class validation that extends PaymentScreen and overrides the validateOrder
    const validation = PaymentScreen =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                var self = this;
                var product_list = [];
                var orderlines = this.env.pos.selectedOrder.orderlines;

                // Checking condition for each order line
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

                    const { confirmed } = await self.showPopup('ConfirmPopup', {
                        title: 'Alert',
                        body: content,
                    });

                    if (confirmed) {
                        super.validateOrder(isForceValidate);
                    }
                } else {
                    super.validateOrder(isForceValidate);
                }
            }
        };

    Registries.Component.extend(PaymentScreen, validation);
    return PaymentScreen;
});



