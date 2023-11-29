odoo.define('advanced_pos_reports.CategorySummaryReceiptScreen', function (require) {
    'use strict';

    const { useRef } = owl;
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const CategorySummaryReceiptScreen = (AbstractReceiptScreen) => {
        class CategorySummaryReceiptScreen extends AbstractReceiptScreen {
              /**
                * @Override AbstractReceiptScreen
              */
             setup() {
                super.setup();
                this.categorySummary = useRef('catgeory-summary');
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
        CategorySummaryReceiptScreen.template = 'CategorySummaryReceiptScreen';
        return CategorySummaryReceiptScreen;
    };
    Registries.Component.addByExtending(CategorySummaryReceiptScreen, AbstractReceiptScreen);
    return CategorySummaryReceiptScreen;
});
