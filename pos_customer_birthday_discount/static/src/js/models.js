odoo.define('point_of_sale.discountOrderLine', function(require) {
    'use strict';

    const field_utils = require('web.field_utils');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');

    models.Orderline = models.Orderline.extend({
        /**
        * Set the discount to order of customer or replaces the current discount with birthday discount to the order placed by the customer.
        *
        * @param {string} discount Discount to be applied
        */
        async set_discount(discount){
            var self = this;
            if(self.pos.config.birthday_discount && self.order.attributes.client){
                var partner_id = self.order.attributes.client.id;
                var first_order = self.pos.config.first_order;
                await rpc.query({model: "pos.config", method: "check_pos_order", args: [[partner_id,first_order]]
                })
                .then(function (data){
                    if(data['birthday'] == 'True' && data['order'] == 'False'){
                        self['check_birthday'] = true
                    }
                    else{
                        self['check_birthday'] = false
                    }
                });
            }
            var parsed_discount = typeof(discount) ===
                    'number' ? discount : isNaN(parseFloat(discount)) ? 0 : field_utils.parse.float('' + discount);
            var disc = Math.min(Math.max(parsed_discount || 0, 0),100);
            this.discount = disc;
            this.discountStr = '' + disc;
            this.trigger('change',this);
        }
    });
});
