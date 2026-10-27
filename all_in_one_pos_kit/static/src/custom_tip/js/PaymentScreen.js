/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    // Tip percentage configured in the POS settings
    get customTipPercentage() {
        return parseFloat(this.pos.config.custom_tip_percentage) || 0;
    },

    get customTipInfo() {
        const percentage = this.customTipPercentage;
        return {
            tip: percentage,
            tip_enable: !!percentage,
        };
    },

    // Order lines of the tip product
    _customTipLines(order) {
        const tipProduct = this.pos.config.tip_product_id;
        if (!tipProduct) {
            return [];
        }
        return order.lines.filter((line) => line.product_id?.id === tipProduct.id);
    },

    async CustomTipButton() {
        const percentage = this.customTipPercentage;
        const order = this.currentOrder;
        const tipProduct = this.pos.config.tip_product_id;
        if (!percentage || !order || !tipProduct) {
            return;
        }
        // base of the percentage: order total without a tip already added
        const tipLines = this._customTipLines(order);
        const tipAmount = tipLines.reduce(
            (sum, line) => sum + (line.priceIncl ?? line.getPriceWithTax?.() ?? 0),
            0
        );
        const total = (order.priceIncl ?? order.getTotalWithTax?.() ?? 0) - tipAmount;
        const suggestedTip = Math.round(((total * percentage) / 100) * 100) / 100;

        this.dialog.add(NumberPopup, {
            title: _t("Tip (%s%%)", percentage),
            startingValue: suggestedTip,
            getPayload: async (payload) => {
                const tip = parseFloat(payload);
                if (isNaN(tip) || tip < 0) {
                    return;
                }
                // replace the tip line added before, if any
                this._customTipLines(order).forEach((line) => order.removeOrderline(line));
                if (tip > 0) {
                    await this.pos.addLineToCurrentOrder(
                        {
                            product_tmpl_id: tipProduct.product_tmpl_id,
                            price_unit: tip,
                        },
                        {},
                        false
                    );
                }
            },
        });
    },
});
