odoo.define('pos_customer_wallet_management.payment_method', function (require) {
    "use strict";
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const {browser} = require("@web/core/browser/browser");
    // Extending PaymentScreen
    const payment_method = PaymentScreen => class extends PaymentScreen {
        /**
         *Override PaymentScreen
         */
        async addNewPaymentLine({detail: paymentMethod}) {
            const orders = this.payment_methods_from_config;
            var current_order = this.env.pos.get_order()
            var order = current_order.attributes.client;
            var select = current_order.selected_orderline;
            if (order == null) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Customer'),
                    body: "Choose Customer First",
                });
            } else if (select == null) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Product'),
                    body: "Choose Product First",
                });
            } else {
                return super.addNewPaymentLine({detail: paymentMethod});
            }
        }

        async validateOrder(isForceValidate) {
            /**
             *Override Validate order button
             */
            var selected_order = this.env.pos.get_order()
            var payment = selected_order.selected_paymentline;
            if (payment.payment_method.wallet_journal) {
                var price = payment.amount;
                var session = this.env.pos.config.current_session_id[1];
                var currency_id = this.env.pos.company.currency_id[1];
                var order = selected_order.attributes.client;
                var wallet_balance = order.wallet_balance;
                var quantity = selected_order.selected_orderline.quantity;
                var balance = wallet_balance - price;
                if (wallet_balance < price) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Unknown'),
                        body: "Not enough wallet balance",
                    });
                } else {
                    var rpc = require('web.rpc');
                    var self = this;
                    rpc.query({
                        model: 'res.partner',
                        method: 'write_value',
                        args: [balance, order, session, price, currency_id],
                    }).then(() => {
                        browser.location.reload();
                        return super.validateOrder(isForceValidate);
                    });
                }
            } else {
                return super.validateOrder(isForceValidate);
            }
        }
    }
    Registries.Component.extend(PaymentScreen, payment_method);
});
