odoo.define('advanced_pos_reports.PaymentSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class PaymentSummaryReceipt extends PosComponent {
         /**
            * @Override PosComponent
         */
        constructor() {
            super(...arguments);
            this._paymentSummaryEnv = this.props.payment_summary
        }
        get payment_summary() {
            //Get payment details
            return this._paymentSummaryEnv;
        }
        get company() {
            //Get company details
            return this.env.pos.company;
        }
        get cashier() {
            //Get cashier details
            return this.env.pos.get_cashier();
        }
    }
    PaymentSummaryReceipt.template = 'PaymentSummaryReceipt';
    Registries.Component.add(PaymentSummaryReceipt);
    return PaymentSummaryReceipt;
});
