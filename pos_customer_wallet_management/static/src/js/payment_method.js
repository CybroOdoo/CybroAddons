/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";


patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },

    async addNewPaymentLine(paymentMethod) {
        var partner = this.currentOrder.get_partner();
        var selected_orderline = this.currentOrder.get_selected_orderline();

        if (!partner) {
            this.env.services.notification.add(_t("Choose Customer First"), { type: 'danger' });
            return;
        }
        else if (!selected_orderline) {
            this.env.services.notification.add(_t("Choose Product First"), { type: 'danger' });
            return;
        }
        else {
            return super.addNewPaymentLine(paymentMethod);
        }
    },

    async validateOrder(isForceValidate) {
        try {
            if (this.currentOrder._walletProcessed) {
                return super.validateOrder(isForceValidate);
            }

            const paymentLines = this.currentOrder.paymentlines || this.currentOrder.payment_ids || [];
            let hasWalletPayment = false;

            for (const paymentLine of paymentLines) {
                const paymentMethod = paymentLine.payment_method || paymentLine.payment_method_id;

                console.log("paymentMethod--->>", paymentMethod);
                debugger

                if (paymentMethod && paymentMethod.wallet_journal) {
                    hasWalletPayment = true;

                    this.currentOrder._walletProcessed = true;
                    var price = paymentLine.amount;
                    var session = this.pos.config.current_session_id[1];
                    var currency_id = this.pos.company.currency_id[1];
                    var partner = this.currentOrder.get_partner();
                    var wallet_balance = partner.wallet_balance;

                    if (wallet_balance < price) {
                        this.currentOrder._walletProcessed = false;
                        this.env.services.notification.add(_t("Not enough wallet balance"), { type: 'danger' });
                        return;
                    } else {
                        try {
                            var balance = wallet_balance - price;
                            var currency_name = this.pos.currency.name;
                            await this.env.services.orm.call("res.partner", "write_value", [balance, partner.id, session, price, currency_name]);

                            partner.wallet_balance = balance;

                            break;
                        } catch (error) {
                            this.currentOrder._walletProcessed = false;
                            this.env.services.notification.add(_t("Failed to update wallet balance"), { type: 'danger' });
                            return;
                        }
                    }
                }
            }
            return super.validateOrder(isForceValidate);

        } catch (error) {
            if (this.currentOrder) {
                this.currentOrder._walletProcessed = false;
            }
            this.env.services.notification.add(_t("An error occurred during order validation"), { type: 'danger' });
        }
    }
});
