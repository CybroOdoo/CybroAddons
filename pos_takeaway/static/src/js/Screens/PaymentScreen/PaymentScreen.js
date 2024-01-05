odoo.define("pos_takeaway.Token", function(require) {
    "use strict";
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    var rpc = require('web.rpc')
//    extending payment screen
    const TokenPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                const order = this.env.pos.get_order();
                var self = this;
                var is_restaurant = self.env.pos.config.module_pos_restaurant
                self.token = 0;
                order.newtoken= self.token
                const syncOrderResult = await this.env.pos.push_single_order(this.currentOrder);
                self.is_take_way = self.env.pos.get_order().is_take_way;
                self.is_restaurant = self.env.pos.config.module_pos_restaurant;
                self.takeaway = self.env.pos.takeaway;
                if (self.is_take_way && self.is_restaurant){
                rpc.query({
                        model: 'pos.order',
                        method: 'generate_token',
                        args: [,syncOrderResult[0].id]
                    }).then(function (result){
                        self.token = result
                        order.token_generated=result
                    });
                }
                await super.validateOrder(isForceValidate);
            }
        };
    Registries.Component.extend(PaymentScreen, TokenPaymentScreen);
    return PaymentScreen;
});
