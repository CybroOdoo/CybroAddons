odoo.define('pos_product_stock.PaymentScreen', function(require) {
    'use strict';
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');
    const Product = PaymentScreen =>
        class extends PaymentScreen {
            //Extend PaymentScreen to super validateOrder  and compute Quantity at the time of validate function
            async validateOrder(isForceValidate) {
                var order = this.env.pos.get_order();
                var lines = order.get_orderlines();
                if (this.env.pos.res_setting['stock_from'] == 'all_warehouse') {
                    if (this.env.pos.res_setting['stock_type'] == 'on_hand') {
                        lines.forEach((quantity) => {
                            var order_quantity = quantity.quantity
                            var new_qty = quantity.product.qty_available - order_quantity
                            quantity.product.qty_available = new_qty
                        })
                    } else if (this.env.pos.res_setting['stock_type'] == 'outgoing_qty') {
                        lines.forEach((quantity) => {
                            var order_quantity = quantity.quantity
                        })
                    } else if (this.env.pos.res_setting['stock_type'] == 'incoming_qty') {
                        lines.forEach((quantity) => {
                            var order_quantity = quantity.quantity
                        })
                    } else if (this.env.pos.res_setting['stock_type'] == 'available_qty') {
                        lines.forEach((quantity) => {
                            var order_quantity = quantity.quantity
                            var available_qty = quantity.product.available_product
                            var new_qty = available_qty - order_quantity
                            quantity.product.available_product = new_qty
                        })
                    }
                } else if (this.env.pos.res_setting['stock_from'] == 'current_warehouse') {
                    if (this.env.pos.res_setting['stock_type'] == 'on_hand') {
                        lines.forEach((line) => {
                            var item_quantity = line.quantity
                            var on_hand_qty = line.product.on_hand
                            var new_qty = on_hand_qty - item_quantity
                            line.product.on_hand = new_qty
                        })
                    } else if (this.env.pos.res_setting['stock_type'] == 'outgoing_qty') {
                        lines.forEach((line) => {
                            var item_quantity = line.quantity
                            var out_going = line.product.outgoing
                        })
                    } else if (this.env.pos.res_setting['stock_type'] == 'incoming_qty') {
                        lines.forEach((line) => {
                            var item_quantity = line.quantity
                            var incoming = line.product.incoming
                        })
                    } else if (this.env.pos.res_setting['stock_type'] == 'available_qty') {
                        lines.forEach((line) => {
                            var item_quantity = line.quantity
                            var available_qty = line.product.available
                            var new_qty = available_qty - item_quantity
                            line.product.available = new_qty
                        })
                    }
                }
                return super.validateOrder(...arguments);
            }
        }
    Registries.Component.extend(PaymentScreen, Product);
    return PaymentScreen;
});
