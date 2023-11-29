odoo.define('advanced_pos_reports.OrderSummaryReceiptScreen', function (require) {
    'use strict';

    const { useRef } = owl;
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const OrderSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class OrderSummaryReceiptScreen extends AbstractReceiptScreen {
            /**
                * @Override AbstractReceiptScreen
            */
            setup() {
                super.setup();
                this.orderSummary = useRef('order-summary');
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
        OrderSummaryReceiptScreen.template = 'OrderSummaryReceiptScreen';
        return OrderSummaryReceiptScreen;
    };
    Registries.Component.addByExtending(OrderSummaryReceiptScreen, AbstractReceiptScreen);
    return OrderSummaryReceiptScreen;
});
