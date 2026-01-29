odoo.define('pos_category_wise_receipt.receipt', function(require) {
    'use strict';
//  Extending OrderReceipt for printing category wise receipts of products
    const OrderReceipt =require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');
    const CategoryOrderReceipt = OrderReceipt =>
        class extends OrderReceipt {
            get orderlines() {
                var order_lines = this.receiptEnv.orderlines;
                var categ = {
                    'category': [],
                    'orderlines': order_lines
                }
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
