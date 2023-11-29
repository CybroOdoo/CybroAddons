odoo.define('advanced_pos_reports.ProductSummaryReceiptScreen', function (require) {
    'use strict';

    const { useRef } = owl;
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const ProductSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class ProductSummaryReceiptScreen extends AbstractReceiptScreen {
            /**
                * @Override AbstractReceiptScreen
            */
            constructor() {
                super(...arguments);
                this.paymentSummary = useRef('product-summary');
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
        ProductSummaryReceiptScreen.template = 'ProductSummaryReceiptScreen';
        return ProductSummaryReceiptScreen;
    };
    Registries.Component.addByExtending(ProductSummaryReceiptScreen, AbstractReceiptScreen);
    return ProductSummaryReceiptScreen;
});
