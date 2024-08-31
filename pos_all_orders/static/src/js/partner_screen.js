/** @odoo-module **/
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(PartnerLine.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    },
    _onClickOrder(id) {
         var self = this;
         var order = this.pos.pos_orders;
         var orders = [];
         for (let i = 0; i < order.length; i++) {
             if (order[i].partner_id[0] == id) {
                 orders.push(order[i]);
             }
         }
         this.pos.showScreen('CustomALLOrdrScreen', {
             orders: orders,
         });
    }
});
