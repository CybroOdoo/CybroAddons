odoo.define('all_in_one_pos_kit.receipt', function(require) {
    'use strict';
    const OrderReceipt =require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');
    const CategoryOrderReceipt = OrderReceipt =>
    class extends OrderReceipt {//Extends the OrderReceipt component to modify the behavior of the orderlines property.
        get orderlines() {//Overrides the orderlines property to categorize the order lines.
            var order_lines = this.receiptEnv.orderlines;
            var categ = {'category': [],'orderlines': order_lines}
            // Iterate over order lines and categorize them based on product category
            for (var i = 0; i <= order_lines.length - 1; i++){
                if(!categ.category.includes(order_lines[i].product.pos_categ_id[1])){
                    categ.category.push(order_lines[i].product.pos_categ_id[1]);
                }
            }
            return categ;
        }
    }
    Registries.Component.extend(OrderReceipt, CategoryOrderReceipt);
    return OrderReceipt;
});
