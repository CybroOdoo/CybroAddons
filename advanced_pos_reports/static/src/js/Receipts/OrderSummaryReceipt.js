odoo.define('advanced_pos_reports.OrderSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class OrderSummaryReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this._orderSummaryEnv = this.props.orders
        }
        get orders() {
            return this._orderSummaryEnv;
        }
        get company() {
            return this.env.pos.company;
        }
        get cashier() {
            return this.env.pos.get_cashier();
        }
        getDate(order) {
            return moment(order.date_order).format('MM-DD-YYYY');
        }
    }
    OrderSummaryReceipt.template = 'OrderSummaryReceipt';

    Registries.Component.add(OrderSummaryReceipt);

    return OrderSummaryReceipt;
});
