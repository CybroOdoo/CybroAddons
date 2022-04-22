odoo.define('advanced_pos_reports.CategorySummaryReceiptScreen', function (require) {
    'use strict';

    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useRef, useContext } = owl.hooks;
    const { useErrorHandlers, onChangeOrder } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const CategorySummaryReceiptScreen = (AbstractReceiptScreen) => {
        class CategorySummaryReceiptScreen extends AbstractReceiptScreen {
            constructor() {
                super(...arguments);
                this.categorySummary = useRef('category-summary');
            }
            confirm() {
                this.showScreen('ProductScreen');
            }
            async printSummary() {
                await this._printReceipt();
            }

        }
        CategorySummaryReceiptScreen.template = 'CategorySummaryReceiptScreen';
        return CategorySummaryReceiptScreen;
    };

    Registries.Component.addByExtending(CategorySummaryReceiptScreen, AbstractReceiptScreen);

    return CategorySummaryReceiptScreen;
});
