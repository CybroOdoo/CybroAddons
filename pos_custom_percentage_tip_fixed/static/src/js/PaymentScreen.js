/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";

patch(PaymentScreen.prototype, {
    get tips() {
        const customTipPercentage = (this.pos && this.pos.config && this.pos.config.custom_tip_percentage) || 0;
        return {
            tip: customTipPercentage,
            tip_enable: Boolean(customTipPercentage),
        };
    },

    // Backward-compatible alias for templates referencing Tips
    get Tips() {
        return this.tips;
    },

    async customTipButton() {
        const tip = this.pos.getTip ? this.pos.getTip() : {};
        const change = Math.abs(this.currentOrder.change || 0);
        const customTipPercentage = (this.pos && this.pos.config && this.pos.config.custom_tip_percentage) || 0;

        this.dialog.add(NumberPopup, {
            title: tip.amount > 0 ? _t("Change Tip") : _t("Add Tip"),
            startingValue: customTipPercentage ? String(customTipPercentage) : (tip.type === "percent" ? String(tip.value || 0) : String(tip.amount || 0)),
            startingType: "percent",
            types: [
                { name: "fixed", symbol: this.pos.currency.symbol },
                { name: "percent", symbol: "%" },
            ],
            getPayload: (newValue, type) =>
                this.onNewTip({ newValue, type, currentTipAmount: tip.amount, change }),
            formatDisplayedValue: (value, type) => {
                if (type === "fixed") {
                    return this.pos.formatCurrency(parseFloat(value) || 0);
                }
                if (type === "percent") {
                    return `${value} %`;
                }
                return value;
            },
        });
    },

    // Backward-compatible alias for templates referencing CustomTipButton
    async CustomTipButton() {
        return this.customTipButton();
    },
});
