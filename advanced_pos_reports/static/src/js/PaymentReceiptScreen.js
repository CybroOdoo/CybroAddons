odoo.define('advanced_pos_reports.PaymentSummaryReceiptScreen', function (require) {
    'use strict';

    const { useRef } = owl;
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const PaymentSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class PaymentSummaryReceiptScreen extends AbstractReceiptScreen {
             /**
                * @Override AbstractReceiptScreen
             */
            constructor() {
                super(...arguments);
                this.paymentSummary = useRef('payment-summary');
            }
            confirm() {
                //Returns to the product screen when we click confirm
                this.showScreen('ProductScreen');
            }
            async printSummary() {
                //Method to print the receipt
                await this._printReceipt();
            }
        }
        PaymentSummaryReceiptScreen.template = 'PaymentSummaryReceiptScreen';
        return PaymentSummaryReceiptScreen;
    };
    Registries.Component.addByExtending(PaymentSummaryReceiptScreen, AbstractReceiptScreen);
    return PaymentSummaryReceiptScreen;
});
