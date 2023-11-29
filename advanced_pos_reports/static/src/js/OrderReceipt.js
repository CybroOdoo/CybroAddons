odoo.define('advanced_pos_reports.OrderSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class OrderSummaryReceipt extends PosComponent {
          /**
            * @Override PosComponent
          */
         setup() {
            super.setup();
            this._orderSummaryEnv = this.props.orders
        }
        get orders() {
            //Get order details
            return this._orderSummaryEnv;
        }
        get company() {
            //Get company details
            return this.env.pos.company;
        }
        get cashier() {
            //Get cashier details
            return this.env.pos.get_cashier();
        }
        getDate(order) {
            //Get date information
            return moment(order.date_order).format('MM-DD-YYYY');
        }
    }
    OrderSummaryReceipt.template = 'OrderSummaryReceipt';
    Registries.Component.add(OrderSummaryReceipt);
    return OrderSummaryReceipt;
});
