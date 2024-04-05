odoo.define('pos_category_wise_receipt.CategoryReceipt', function(require) {
    'use strict';
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');
    /** Extends OrderReceipt to make change in pos receipt **/
    const CategoryOrderReceipt = OrderReceipt =>
        class extends OrderReceipt {
        /** Gets the order lines while enter validate button from the pos payment screen **/
        get orderlines() {
            var order_lines = this.receiptEnv.orderlines;
            var category = {
                'category': [],
                'orderlines': order_lines
            }
            for(var i = 0; i <= order_lines.length - 1; i++) {
                if(!category.category.includes(order_lines[i].product.pos_categ_id[1])) {
                    category.category.push(order_lines[i].product.pos_categ_id[1]);
                }
            }
            return category;
        }
     }
     Registries.Component.extend(OrderReceipt, CategoryOrderReceipt);
     return OrderReceipt;
   });
