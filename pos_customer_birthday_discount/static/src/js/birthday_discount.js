odoo.define('point_of_sale.BirthdayDiscount', function(require) {
    'use strict';

    const ActionpadWidget = require('point_of_sale.ActionpadWidget');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');

    const BirthdayDiscount = (ActionpadWidget) =>
    class extends ActionpadWidget{
        /**
        * isLong function is inherited to check if the current day is the birthday
        * of selected partner and return the result.
        * constructor is used to make the function async
        */
        constructor() {
            super(...arguments);
            Object.defineProperty(this,'isLongName', {
                get: async function() {
                    var self = this
                    if(self.env.pos.config.birthday_discount && self.props.client){
                        self.client['disc'] = 0 ;
                        var orderLines = self.env.pos.attributes.selectedOrder.orderlines.models;
                        rpc.query({model: "pos.config", method: "check_birthday", args: [self.props.client.id]
                        }).then(function (data) {
                            if(data['birthday']){
                               self.client['birthday'] = 'True';
                               self.client['disc'] = self.env.pos.config.discount * 100;
                            }
                            for(var order_id=0; order_id<orderLines.length; order_id++){
                                orderLines[order_id].set_discount(self.client['disc']);
                            }
                        });
                    }
                    return this.client && this.client.name.length > 10;
                }
            });
        }
    }
    Registries.Component.extend(ActionpadWidget, BirthdayDiscount);
});
