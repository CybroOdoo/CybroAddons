/** @odoo-module */

import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { parseFloat as oParseFloat } from "@web/views/fields/parsers";
import { useService } from "@web/core/utils/hooks";


patch(Orderline.prototype, {

    getDisplayData() {
        return {
            ...super.getDisplayData(),
            check_birthday: this.check_birthday,

        };
    },

        async set_discount(discount){
        var disc;
        /**Original code of set_discount function*/
        var parsed_discount =
            typeof discount === "number"
                ? discount
                : isNaN(parseFloat(discount))
                ? 0
                : oParseFloat("" + discount);
        disc = Math.min(Math.max(parsed_discount || 0, 0), 100);
        this.discount = disc;
        this.discountStr = "" + disc;
        /**Extended code for birthday discount functions*/
        if(this.pos.config.birthday_discount && this.order.partner){
            var partner_id = this.order.partner.id;
            var first_order = this.pos.config.first_order;
            const result = await this.env.services.orm.call("pos.config", "check_pos_order", [partner_id,first_order])
                if(result['birthday'] === 'True' && result['order'] === 'False'){
                    this.check_birthday = true
                }
                else{
                    this.check_birthday = false
                }
        }
    }
});
