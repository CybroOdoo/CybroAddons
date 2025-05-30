odoo.define('all_in_one_pos_kit.OrderReceipt', function(require) {
    'use strict';
    var { Order } = require('point_of_sale.models');
    var Registries = require('point_of_sale.Registries');
    // Extends the Order model to include additional information in the exported data for receipt.
    const OrderLineCount = (Order) => class CustomOrder extends Order {
        export_for_printing() {
        //Overrides the export_for_printing() method to include the count and sum of order lines. @returns {Object} - The modified order data for receipt.
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
