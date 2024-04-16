/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async afterOrderValidation(suggestToSync = true) {
    //---remaining points calculated after claiming the reward is shown in the redemption history
        const res = super.afterOrderValidation(...arguments);
        if(this.pos.get_order().pointsCost != undefined){
            const order = this.pos.get_order()
            const coupon = order.selectedCoupon
            let pointsOfPartner = 0
            if(order.partner.loyalty_cards.length != undefined){
                pointsOfPartner += order.partner.loyalty_cards[coupon].points
            }
            const pointsWon = order.couponPointChanges[coupon].points
            const pointsSpent = order.pointsCost
            const balance = pointsOfPartner + pointsWon - pointsSpent
            const token = order.access_token
            const remaining_points = this.env.services.orm.call('pos.order.line','remaining_points',[[balance],[token]])
        }
        return res
    },
});
