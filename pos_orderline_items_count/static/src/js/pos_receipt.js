odoo.define('pos_orderline_items_count.OrderReceipt', function(require) {
    'use strict';

    var { Order } = require('point_of_sale.models');
    var Registries = require('point_of_sale.Registries');

    const OrderLineCount = (Order) => class CustomOrder extends Order {
        export_for_printing() {
            var result = super.export_for_printing(...arguments);
            result.count = this.orderlines.length;
            var sum = 0;
            this.orderlines.forEach(function(t) {
                sum += t.quantity;
            })
            result.sum = sum
            return result;
            }
        }
        Registries.Model.extend(Order, OrderLineCount);
    });