odoo.define('advanced_pos_reports.ProductSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class ProductSummaryReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this._productSummaryEnv = this.props.products
        }
        get products() {
            return this._productSummaryEnv;
        }
        get company() {
            return this.env.pos.company;
        }
        get cashier() {
            return this.env.pos.get_cashier();
        }
    }
    ProductSummaryReceipt.template = 'ProductSummaryReceipt';

    Registries.Component.add(ProductSummaryReceipt);

    return ProductSummaryReceipt;
});
