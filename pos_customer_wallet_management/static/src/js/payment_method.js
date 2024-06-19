odoo.define('pos_customer_wallet_management.payment_method', function (require) {
"use strict";
const Registries = require('point_of_sale.Registries');
const PaymentScreen = require('point_of_sale.PaymentScreen');
const { browser } = require("@web/core/browser/browser");

const payment_method = (PaymentScreen) =>
  class extends PaymentScreen {
       /**
         *Override PaymentScreen
       */
       async addNewPaymentLine({ detail: paymentMethod }) {
                                       console.log(this.env.pos.selectedOrder.partner, 'addNewPaymentLine......................')
              const orders = this.payment_method;
              var order = this.env.pos.selectedOrder.partner;
              var select = this.env.pos.selectedOrder.selected_orderline;
              var payment = this.env.pos.selectedOrder.selected_paymentline;
                  if (order == null) {
                       await this.showPopup('ErrorPopup', {
                            title: this.env._t('Unknown'),
                            body: "Choose Customer First",
                        });
                  }
                  else if (select == null) {
                       await this.showPopup('ErrorPopup', {
                                title: this.env._t('Product'),
                                body: "Choose Product First",
                       });
                  }
                  else {
                         return super.addNewPaymentLine({ detail: paymentMethod });
                  }
   }
   async validateOrder(isForceValidate) {
                 /**
                    *Override Validate order button
                 */
                  var payment = this.env.pos.selectedOrder.paymentlines;
                     for (const orderLine of payment) {
                         if (orderLine.payment_method.wallet_journal) {
                            var price = orderLine.amount;
                            var session = this.env.pos.config.current_session_id[1];
                            var currency_id = this.env.pos.company.currency_id[1];
                            var order = this.env.pos.selectedOrder.partner;
                            var wallet_balance = this.env.pos.selectedOrder.partner.wallet_balance;
                            var quantity = this.env.pos.selectedOrder.selected_orderline.quantity;
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
                         }
                         else {
                               return super.validateOrder(isForceValidate);
                         }
                     }
   }
}
  Registries.Component.extend(PaymentScreen, payment_method);
});
