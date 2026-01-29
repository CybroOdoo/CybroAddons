odoo.define('advanced_loyalty_management.LoyaltyPrograms', function (require) {
    "use strict";

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const rpc = require('web.rpc');
    const { _t } = require('web.core');

    class LoyaltyPrograms extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        async convertToLoyalty(props, programId) {
            const change = props.change;
            const order = props.Order;
            const loyalty = props.Loyalty

            // Resets the change by adjusting the payment
            if (change > 0) {
                const lastPaymentLine = props.Order.get_paymentlines().slice(-1)[0];
                if (lastPaymentLine) {
                    lastPaymentLine.set_amount(lastPaymentLine.get_amount() - change);
                }
                order.change_to_loyalty = change * loyalty.point_rate;
            }

            this.trigger('confirm');
        }
    }

    LoyaltyPrograms.template = 'LoyaltyPrograms';
    LoyaltyPrograms.defaultProps = {
        confirmText: _t('Confirm'),
        cancelText: _t('Cancel'),
        title: _t('Loyalty Programs'),
        body: '',
    };

    Registries.Component.add(LoyaltyPrograms);

    return LoyaltyPrograms;
});
