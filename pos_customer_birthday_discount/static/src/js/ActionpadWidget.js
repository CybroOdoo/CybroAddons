odoo.define('point_of_sale.BirthdayDiscount', function(require) {
    'use strict';
    const ActionpadWidget = require('point_of_sale.ActionpadWidget');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const { useState } = owl.hooks;
    /**
    * isLong function is inherited to check if the current day is the birthday
    * of selected partner and return the result.
    */
    const BirthdayDiscount = (ActionpadWidget) =>
    class extends ActionpadWidget{
        constructor(){
            super(...arguments);
            this.state = useState({birthday: 0 });
            Object.defineProperty(this,'isLongName', {
                get: async function() {
                    var self = this
                    var orderLines = self.env.pos.attributes.selectedOrder.orderlines.models;
                    if(self.env.pos.config.birthday_discount && self.props.client){
                        self.client['disc'] = 0 ;
                        rpc.query({model: "pos.config", method: "check_birthday", args: [self.props.client.id]
                        }).then(function (data) {
                            if(data['birthday']){
                               self.client.birthday = true;
                               self.client['disc'] = self.env.pos.config.discount * 100;
                            }
                            for(var order_id=0; order_id<orderLines.length; order_id++){
                                orderLines[order_id].set_discount(self.client['disc']);
                            }
                        });
                    }
                    else{
                        for(var order_id=0; order_id<orderLines.length; order_id++){
                                orderLines[order_id].set_discount(0);
                        }
                    }
                    return this.client && this.client.name.length > 10;
                }
            });
        }
    }
    Registries.Component.extend(ActionpadWidget, BirthdayDiscount);
});
