/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    },
    async validateOrder(isForceValidate) {
        try {
            this.numberBuffer.capture();
            if (this.pos.config.cash_rounding) {
                if (!this.pos.get_order().check_paymentlines_rounding()) {
                    this.popup.add(ErrorPopup, {
                        title: _t("Rounding error in payment lines"),
                        body: _t(
                            "The amount of your payment lines must be rounded to validate the transaction."
                        ),
                    });
                    return false;
                }
            }
            const order = this.pos.get_order();
            await super.validateOrder(...arguments);
            const orderLinesData = (order.orderlines || [])
            .filter(orderLine => orderLine.coupon_id)
            .map(orderLine => ({
                coupon_id: orderLine.coupon_id,
                point_cost: orderLine.points_cost || orderLine.point_cost || 0,
            }));
            if (orderLinesData.length > 0) {
                try {
                    const result = await this.orm.call(
                        'pos.order',
                        'set_remaining_balance',
                        [orderLinesData],
                        {}
                    );
                    if (!result) {
                        console.warn('Failed to update coupon balances');
                    }
                } catch (error) {
                    console.error('Error updating coupon balances:', error);
                }
            }
            if (await this._isOrderValid(isForceValidate)) {
                this.paymentLines
                    .filter(line => !line.is_done())
                    .forEach(line => this.currentOrder.remove_paymentline(line));

                await this._finalizeValidation();
                return true;
            }
            return false;
        } catch (error) {
            console.error("Order validation failed:", error);
            this.popup.add(ErrorPopup, {
                title: _t("Validation Error"),
                body: _t("An error occurred while validating the order."),
            });
            return false;
        }
    },
});