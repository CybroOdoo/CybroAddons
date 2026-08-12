/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { parseFloat } from "@web/views/fields/parsers";
import { floatIsZero } from "@web/core/utils/numbers";
import {
    getOrderCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(PaymentScreen.prototype, {
    async addTip() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.addTip(...arguments);
        }

        const tip = this.currentOrder.get_tip();
        const change = this.currentOrder.get_change();
        const value = tip === 0 && change > 0 ? change : tip;
        const currency = getOrderCurrency(this.currentOrder) || this.pos.currency;
        this.dialog.add(NumberPopup, {
            title: tip ? _t("Change Tip") : _t("Add Tip"),
            startingValue: this.env.utils.formatCurrency(value, false, currency),
            formatDisplayedValue: (inputValue) =>
                this.env.utils.formatCurrency(parseFloat(inputValue || 0), currency),
            getPayload: async (inputValue) => {
                await this.pos.set_tip(parseFloat(inputValue ?? ""));
            },
        });
    },

    async sendPaymentRequest(line) {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.sendPaymentRequest(...arguments);
        }

        this.pos.paymentTerminalInProgress = true;
        this.numberBuffer.capture();
        this.paymentLines.forEach((paymentLine) => {
            paymentLine.can_be_reversed = false;
        });

        let isPaymentSuccessful = false;
        if (line.payment_method_id.payment_method_type === "qr_code") {
            const response = await this.pos.showQR(line);
            isPaymentSuccessful = line.handle_payment_response(response);
        } else {
            isPaymentSuccessful = await line.pay();
        }

        this.pos.paymentTerminalInProgress = false;
        const currentOrder = line.pos_order_id;
        const currency = getOrderCurrency(currentOrder) || this.pos.currency;
        if (
            isPaymentSuccessful &&
            currentOrder.is_paid() &&
            floatIsZero(currentOrder.get_due(), currency.decimal_places) &&
            this.pos.config.auto_validate_terminal_payment
        ) {
            this.validateOrder(false);
        }
    },
});
