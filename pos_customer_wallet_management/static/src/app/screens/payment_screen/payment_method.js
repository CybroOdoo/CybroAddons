import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
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
});

patch(OrderPaymentValidation.prototype, {
    // Total of all wallet payment lines on the order
    getWalletAmount() {
        let total = 0;
        for (const line of this.paymentLines) {
            const method = line.payment_method_id;
            const isWallet =
                method &&
                (method.is_wallet_journal ||
                    (method.name || "").toLowerCase().includes("wallet"));
            if (isWallet) {
                total += Number(line.amount || 0);
            }
        }
        return total;
    },

    // 1) Block the order if the wallet balance is not enough
    async isOrderValid(isForceValidate) {
        const walletAmount = this.getWalletAmount();
        if (walletAmount > 0) {
            const partner = this.order.getPartner();
            const notification = this.pos.env.services.notification;
            if (!partner) {
                notification.add(_t("Choose Customer First"), { type: "danger" });
                return false;
            }
            if (Number(partner.wallet_balance || 0) < walletAmount) {
                notification.add(_t("Not enough wallet balance"), { type: "danger" });
                return false;
            }
        }
        return super.isOrderValid(isForceValidate);
    },

    // 2) Deduct the balance only after the order was validated
    async validateOrder(isForceValidate) {
        const order = this.order;
        if (order._walletProcessed) {
            return super.validateOrder(isForceValidate);
        }
        const walletAmount = this.getWalletAmount();
        const partner = order.getPartner();
        const result = await super.validateOrder(isForceValidate);

        if (result && walletAmount > 0 && partner) {
            order._walletProcessed = true;
            try {
                const newBalance = Number(partner.wallet_balance || 0) - walletAmount;
                await this.pos.env.services.orm.call("res.partner", "write_value", [
                    newBalance,
                    partner.id,
                    this.pos.session?.id || false,
                    walletAmount,
                    this.pos.currency.name,
                    order.uuid || order.name,
                ]);
                partner.wallet_balance = newBalance;
            } catch (error) {
                order._walletProcessed = false;
                this.pos.env.services.notification.add(
                    _t("Failed to update wallet balance"),
                    { type: "danger" }
                );
            }
        }
        return result;
    },
});
