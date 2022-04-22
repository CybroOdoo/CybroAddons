odoo.define('advanced_pos_reports.SessionSummaryReceiptScreen', function (require) {
    'use strict';

    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useRef, useContext } = owl.hooks;
    const { useErrorHandlers, onChangeOrder } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const SessionSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class SessionSummaryReceiptScreen extends AbstractReceiptScreen {
            constructor() {
                super(...arguments);
                this.paymentSummary = useRef('product-summary');
            }
            confirm() {
                this.showScreen('ProductScreen');
            }
            async printSummary() {
                await this._printReceipt();
            }
        }
        SessionSummaryReceiptScreen.template = 'SessionSummaryReceiptScreen';
        return SessionSummaryReceiptScreen;
    };

    Registries.Component.addByExtending(SessionSummaryReceiptScreen, AbstractReceiptScreen);

    return SessionSummaryReceiptScreen;
});
