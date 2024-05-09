odoo.define('pos_orderline_items_count.OrderReceipt', function(require) {
    'use strict';

    const OrderReceipt = require('point_of_sale.OrderReceipt')
    const Registries = require('point_of_sale.Registries');
    var { Order } = require('point_of_sale.models');
    const OrderReceiptCount = OrderReceipt =>
    //    extending the pos receipt screen
        class extends OrderReceipt {
        get receiptEnv() {
                let receipt_render_env = super.receiptEnv;
                let receipt = receipt_render_env.receipt;
                receipt.count = this._receiptEnv.orderlines.length;
                var sum = 0;
                this._receiptEnv.orderlines.forEach(function(t) {
                    sum += t.quantity;
                })
                receipt.sum = sum
                return receipt_render_env;
            }
        }
        Registries.Component.extend(OrderReceipt, OrderReceiptCount);
        return OrderReceiptCount
    });
