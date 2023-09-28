/** @odoo-module */

import { Orderline } from 'point_of_sale.models';
import Registries from "point_of_sale.Registries";
import field_utils from 'web.field_utils';
import rpc from 'web.rpc';


const discount = (Orderline) =>
class extends Orderline{
    /**
    * Set the discount to order of customer or replaces the current discount with birthday discount to the order placed by the customer.
    *
    * @param {string} discount Discount to be applied
    */
    async set_discount(discount){
        var disc;
        /**Original code of set_discount function*/
        var parsed_discount = typeof(discount) === 'number' ? discount : isNaN(parseFloat(discount)) ? 0 : field_utils.parse.float('' + discount);
        disc = Math.min(Math.max(parsed_discount || 0, 0),100);
        this.discount = disc;
        this.discountStr = '' + disc;
        /**Extended code for birthday discount functions*/
        var self = this;
        if(self.pos.config.birthday_discount && self.order.partner){
            var partner_id = self.order.partner.id;
            var first_order = self.pos.config.first_order;
            await rpc.query({model: "pos.config", method: "check_pos_order", args: [partner_id,first_order]
                })
            .then(function (data) {
                if(data['birthday'] == 'True' && data['order'] == 'False'){
                    self['check_birthday'] = true
                }
                else{
                    self['check_birthday'] = false
                }
            });
        }
    }
}
Registries.Model.extend(Orderline, discount);
