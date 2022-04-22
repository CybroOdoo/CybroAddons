odoo.define('advanced_pos_reports.CategorySummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class CategorySummaryButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this._onClick);
        }
        _onClick() {
            this.showPopup('CategorySummaryPopup', { title: 'Category Summary', });
        }
    }
    CategorySummaryButton.template = 'advanced_pos_reports.CategorySummaryButton';

    ProductScreen.addControlButton({
        component: CategorySummaryButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(CategorySummaryButton);

    return CategorySummaryButton;
});