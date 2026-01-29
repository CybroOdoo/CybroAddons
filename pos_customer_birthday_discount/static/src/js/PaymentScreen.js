odoo.define('point_of_sale.BirthdayPaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    /**
    * selectClient function is inherited to check if the current day is the birthday
    * of selected partner and apply the discount.
    */
    const BirthdayPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async selectClient() {
                // IMPROVEMENT: This code snippet is repeated multiple times.
                // Maybe it's better to create a function for it.
                const currentClient = this.currentOrder.get_client();
                const { confirmed, payload: newClient } = await this.showTempScreen(
                    'ClientListScreen',
                    { client: currentClient }
                );
                if (confirmed) {
                    var val = 0;
                    var orderLines = this.currentOrder.orderlines
                    if(newClient){
                        var first_order = this.env.pos.config.first_order;
                        var self = this;
                        await rpc.query({model: "pos.config", method: "check_pos_order", args: [[newClient['id'],first_order]]
                        })
                        .then(function (data) {
                            if(data['birthday'] == 'True' && data['order'] == 'False'){
                                val = self.env.pos.config.discount * 100;
                            }
                        });
                    }
                    for(var order_id=0; order_id<orderLines.length; order_id++){
                        orderLines.models[order_id].discount = val;
                        orderLines.models[order_id].discountStr = '' + val;
                    }
                    this.currentOrder.set_client(newClient);
                    this.currentOrder.updatePricelist(newClient);
                }
            }
        }
    Registries.Component.extend(PaymentScreen, BirthdayPaymentScreen);
    return PaymentScreen;
})
