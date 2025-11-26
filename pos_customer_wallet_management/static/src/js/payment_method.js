/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
        async addNewPaymentLine(paymentMethod) {
        const orders = this.pos.payment_methods;
        var order = this.pos.selectedOrder.partner;
        var select = this.pos.selectedOrder.selected_orderline
        if (order == null) {
            await this.popup.add(ErrorPopup, {
                title: _t('Unknown'),
                body: "Choose Customer First",
            });
        }
        else if (select == null) {
             await this.popup.add(ErrorPopup, {
                  title: _t('Product'),
                  body: "Choose Product First",
             });
        }
        else {
              return super.addNewPaymentLine(paymentMethod);
        }
    },
    async validateOrder(isForceValidate) {
       var payment = this.pos.selectedOrder.paymentlines;
       for (const orderLine of payment) {
       if (orderLine.payment_method.wallet_journal) {
             var price = orderLine.amount;
             var session = this.pos.config.current_session_id[1];
             var currency_id = this.pos.company.currency_id[1];
             var order = this.pos.selectedOrder.partner;
             var wallet_balance = this.pos.selectedOrder.partner.wallet_balance;
             var quantity = this.pos.selectedOrder.selected_orderline.quantity;
             var balance = wallet_balance - price;
             console.log('balance',balance, wallet_balance, price)
             if (wallet_balance < price) {
                 await this.popup.add(ErrorPopup, {
                 title: _t('Unknown'),
                 body: "Not enough wallet balance",
                 });
             }else {
                    var self = this;
                    await this.orm.call("res.partner", "write_value", [balance, order, session, price, currency_id]).then(() =>
                    {
                       browser.location.reload();
                       return super.validateOrder(isForceValidate)
                    });
             }
       }
       else {
              return super.validateOrder(isForceValidate);
             }
       }
    }
});