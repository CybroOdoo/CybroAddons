odoo.define('advanced_pos_reports.PaymentSummaryReceiptScreen', function (require) {
    'use strict';

    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useRef, useContext } = owl.hooks;
    const { useErrorHandlers, onChangeOrder } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const PaymentSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class PaymentSummaryReceiptScreen extends AbstractReceiptScreen {
            constructor() {
                super(...arguments);
                this.paymentSummary = useRef('payment-summary');
            }
            confirm() {
                this.showScreen('ProductScreen');
            }
            async printSummary() {
                await this._printReceipt();
            }
        }
        PaymentSummaryReceiptScreen.template = 'PaymentSummaryReceiptScreen';
        return PaymentSummaryReceiptScreen;
    };

    Registries.Component.addByExtending(PaymentSummaryReceiptScreen, AbstractReceiptScreen);

    return PaymentSummaryReceiptScreen;
});
