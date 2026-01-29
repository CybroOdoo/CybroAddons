odoo.define('pos_takeaway.OrderReceipt', function(require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    var rpc = require('web.rpc')
//    Extends OrderReceipt to assign the takeaway value and the token.
    const OrderReceiptToken = OrderReceipt =>
    class extends OrderReceipt {
        async willUpdateProps(nextProps) {
            super.willUpdateProps(nextProps)
            var self = this;
            self.token = 0;
            self.is_take_way = self.env.pos.get_order().is_take_way;
            self.is_restaurant = self.env.pos.config.module_pos_restaurant;
            self.takeaway = self.env.pos.takeaway;
            if (self.is_take_way && self.is_restaurant){
                await rpc.query({
                    model: 'pos.order',
                    method: 'generate_token',
                    args: [,this.env.pos.get_order_with_uid()
                    ],
                }).then(function (result){
                    self.token = result
                });
            }
        }
    }
    Registries.Component.extend(OrderReceipt, OrderReceiptToken);
    return OrderReceipt;
});