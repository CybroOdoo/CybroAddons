odoo.define('advanced_pos_reports.OrderSummaryReceiptScreen', function (require) {
    'use strict';

    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useRef, useContext } = owl.hooks;
    const { useErrorHandlers, onChangeOrder } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const OrderSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class OrderSummaryReceiptScreen extends AbstractReceiptScreen {
            constructor() {
                super(...arguments);
                this.orderSummary = useRef('order-summary');
            }
            confirm() {
                this.showScreen('ProductScreen');
            }
            async printSummary() {
                await this._printReceipt();
            }

        }
        OrderSummaryReceiptScreen.template = 'OrderSummaryReceiptScreen';
        return OrderSummaryReceiptScreen;
    };

    Registries.Component.addByExtending(OrderSummaryReceiptScreen, AbstractReceiptScreen);

    return OrderSummaryReceiptScreen;
});
