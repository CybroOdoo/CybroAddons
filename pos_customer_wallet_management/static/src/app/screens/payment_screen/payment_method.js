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
        var partner = this.currentOrder.getPartner();
        var selected_orderline_uuid = this.currentOrder.uiState.selected_orderline_uuid;
        if (!partner) {
            this.env.services.notification.add(_t("Choose Customer First"), { type: 'danger' });
            return;
        }
        else if (!selected_orderline_uuid) {
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
            let walletAmount = 0;
            const partner = this.currentOrder.getPartner();
            const orderRef = this.currentOrder.uuid || this.currentOrder.name;
            for (const paymentLine of paymentLines) {
                const paymentMethod = paymentLine.payment_method || paymentLine.payment_method_id;
                const isWalletPayment = paymentMethod && (
                    paymentMethod.is_wallet_journal ||
                    (paymentMethod.name || "").toLowerCase().includes("wallet")
                );
                if (isWalletPayment) {
                    walletAmount += Number(paymentLine.amount || 0);
                }
            }
            if (walletAmount > 0) {
                this.currentOrder._walletProcessed = true;
                const wallet_balance = Number(partner.wallet_balance || 0);
                if (wallet_balance < walletAmount) {
                    this.currentOrder._walletProcessed = false;
                    this.env.services.notification.add(_t("Not enough wallet balance"), { type: 'danger' });
                    return;
                }
                try {
                    const balance = wallet_balance - walletAmount;
                    const sessionId = this.pos.config.current_session_id?.[0] || false;
                    const currencyName = this.pos.currency.name;
                    await this.env.services.orm.call("res.partner", "write_value", [
                        balance,
                        partner.id,
                        sessionId,
                        walletAmount,
                        currencyName,
                        orderRef,
                    ]);
                    partner.wallet_balance = balance;
                } catch (error) {
                    this.currentOrder._walletProcessed = false;
                    this.env.services.notification.add(_t("Failed to update wallet balance"), { type: 'danger' });
                    return;
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
