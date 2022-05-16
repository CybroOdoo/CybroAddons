odoo.define('advanced_pos_reports.CategorySummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class CategorySummaryReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this._categorySummaryEnv = this.props.categories
        }
        get categories() {
            return this._categorySummaryEnv;
        }
        get company() {
            return this.env.pos.company;
        }
        get cashier() {
            return this.env.pos.get_cashier();
        }
    }
    CategorySummaryReceipt.template = 'CategorySummaryReceipt';

    Registries.Component.add(CategorySummaryReceipt);

    return CategorySummaryReceipt;
});
