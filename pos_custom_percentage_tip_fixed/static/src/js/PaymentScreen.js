/** @odoo-module **/
/*
    Cybrosys Technologies Pvt. Ltd.
    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
*/

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(PaymentScreen.prototype, {
    async customTipButton() {
        const customTipPercentage = parseFloat(this.pos.config.custom_tip_percentage) || 0;
        if (!customTipPercentage) {
            return;
        }

        const tipPercent = customTipPercentage / 100;
        const currentTipAmount = this.currentOrder.getTip() || 0;
        const baseTotal = this.currentOrder.totalDue - currentTipAmount;
        const customTip = baseTotal * tipPercent;
        const change = Math.abs(this.currentOrder.change || 0);
        const startingValue = customTip === 0 && change > 0 ? change : customTip;

        const payload = await makeAwaitable(this.dialog, NumberPopup, {
            title: customTip ? _t("Change Tip") : _t("Add Tip"),
            startingValue: this.env.utils.formatCurrency(startingValue, false),
            formatDisplayedValue: (x) => `${this.pos.currency.symbol} ${x}`,
        });

        if (payload === undefined) {
            return;
        }

        const newTip = parseFloat(payload) || 0;
        const tipDifference = newTip - currentTipAmount;
        if (tipDifference === 0) {
            return;
        }

        const tipToAdd = change <= 0 ? tipDifference : Math.max(0, tipDifference - change);
        await this.pos.setTip(newTip);

        const targetPaymentLine =
            this.selectedPaymentLine ||
            (this.paymentLines && this.paymentLines.length > 0
                ? this.paymentLines.at(-1)
                : null);

        if (targetPaymentLine) {
            targetPaymentLine.setAmount(targetPaymentLine.getAmount() + tipToAdd);
        }
    },

    // Backward compatibility for callers referencing PascalCase
    async CustomTipButton() {
        return this.customTipButton();
    },

    get Tips() {
        const percentage = this.pos.config.custom_tip_percentage || 0;
        return {
            tip: percentage,
            tip_enable: Boolean(percentage),
        };
    },

    get tips() {
        return this.Tips;
    },
});