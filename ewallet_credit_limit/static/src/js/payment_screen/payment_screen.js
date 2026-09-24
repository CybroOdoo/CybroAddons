odoo.define('ewallet_credit_limit.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { useService } = require('@web/core/utils/hooks');

    const PosCreditPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            setup() {
                super.setup();
                this.rpc = useService('rpc');
            }
            async validateOrder(isForceValidate) {
                if (this.env.pos.config.cash_rounding) {
                    if (!this.env.pos.get_order().check_paymentlines_rounding()) {
                        this._display_popup_error_paymentlines_rounding();
                        return;
                    }
                }
                const order = this.env.pos.get_order();
                const orderLinesData = order.get_orderlines()
                    .filter((orderLine) => orderLine.coupon_id)
                    .map((orderLine) => ({
                        coupon_id: orderLine.coupon_id,
                        point_cost: orderLine.points_cost || 0,
                    }));
                if (orderLinesData.length > 0) {
                    try {
                        const result = await this.rpc({
                            model: 'pos.order',
                            method: 'set_remaining_balance',
                            args: [orderLinesData],
                        });
                    } catch (error) {
                        this.showPopup('ErrorPopup', {
                            title: 'Error',
                            body: 'Failed to process the order. Please try again.',
                        });
                        return;
                    }
                }
                if (await this._isOrderValid(isForceValidate)) {
                    for (const line of this.paymentLines) {
                        if (!line.is_done()) {
                            order.remove_paymentline(line);
                        }
                    }
                    await this._finalizeValidation();
                }
            }
        };
    Registries.Component.extend(PaymentScreen, PosCreditPaymentScreen);
    return PosCreditPaymentScreen;
});