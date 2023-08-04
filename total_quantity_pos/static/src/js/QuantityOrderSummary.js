odoo.define('total_quantity_pos.OrderSummary', function(require) {
    'use strict';

    const OrderSummary = require('point_of_sale.OrderSummary');
    const Registries = require('point_of_sale.Registries');

    const QuantityChange =  (OrderSummary) => class extends OrderSummary {
         getTotal() {

         //  Get total number of items and quantities of
         //  products from the orderlines.

             var result = super.getTotal(...arguments);
             var total_items = this.props.order.orderlines.length;
             let quant_count = 0;
             let i = 0 ;
             for( ; i < total_items; ){
                  quant_count += this.props.order.orderlines[i].quantity
                   i++;
             }
             this.props.total_quantity = quant_count;
         return result;
        }
    }
    Registries.Component.extend(OrderSummary, QuantityChange)
});
