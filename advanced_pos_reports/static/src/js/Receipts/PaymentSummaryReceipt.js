odoo.define('advanced_pos_reports.PaymentSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class PaymentSummaryReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this._paymentSummaryEnv = this.props.payment_summary
        }
        get payment_summary() {
            return this._paymentSummaryEnv;
        }
        get company() {
            return this.env.pos.company;
        }
        get cashier() {
            return this.env.pos.get_cashier();
        }
//        getDate(order) {
//            return moment(order.date_order).format('MM-DD-YYYY');
//        }
    }
    PaymentSummaryReceipt.template = 'PaymentSummaryReceipt';

    Registries.Component.add(PaymentSummaryReceipt);

    return PaymentSummaryReceipt;
});
