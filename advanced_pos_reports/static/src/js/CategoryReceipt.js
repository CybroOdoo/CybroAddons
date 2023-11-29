odoo.define('advanced_pos_reports.CategorySummaryReceipt', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class CategorySummaryReceipt extends PosComponent {
          /**
            * @Override PosComponent
          */
         setup() {
            super.setup();
            this._categorySummaryEnv = this.props.categories
            this.categories_line = this.props.categories;
         }
         get categories() {
             //Get the category details
             return this._categorySummaryEnv;
         }
         get company() {
            //Get the company details
            return this.env.pos.company;
         }
         get cashier() {
            //Get cashier details
            return this.env.pos.get_cashier();
         }
    }
    CategorySummaryReceipt.template = 'CategorySummaryReceipt';
    Registries.Component.add(CategorySummaryReceipt);
    return CategorySummaryReceipt;
});
