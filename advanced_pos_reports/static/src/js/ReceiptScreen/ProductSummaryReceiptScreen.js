odoo.define('advanced_pos_reports.ProductSummaryReceiptScreen', function (require) {
    'use strict';

    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useRef, useContext } = owl.hooks;
    const { useErrorHandlers, onChangeOrder } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const ProductSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class ProductSummaryReceiptScreen extends AbstractReceiptScreen {
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
        ProductSummaryReceiptScreen.template = 'ProductSummaryReceiptScreen';
        return ProductSummaryReceiptScreen;
    };

    Registries.Component.addByExtending(ProductSummaryReceiptScreen, AbstractReceiptScreen);

    return ProductSummaryReceiptScreen;
});
