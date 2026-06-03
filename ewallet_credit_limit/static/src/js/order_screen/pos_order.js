/** @odoo-module **/

import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {

    /**
     * @returns {number} The points that are left for the given coupon for this order.
     */
     _getRealCouponPoints(coupon_id) {
        let points = 0;
        const dbCoupon = this.pos.couponCache[coupon_id];
        if (!dbCoupon) return points;
        points = dbCoupon.balance || 0;

        if (this.pos.loyalty_card && coupon_id) {
            const matchedCard = this.pos.loyalty_card.find((card) => {
                return card.id == coupon_id;
            });
            if (matchedCard && matchedCard.set_limit === true) {
                points = matchedCard.balance_limit_amount || 0;
            } else if (matchedCard) {
                points = dbCoupon.balance;
            }
        }
        Object.values(this.couponPointChanges).some((pe) => {
            if (pe.coupon_id === coupon_id) {
                if (this.pos.program_by_id[pe.program_id].applies_on !== "future") {
                    points += pe.points || 0;
                }
                return true;
            }
            return false;
        });
        for (const line of this.get_orderlines()) {
            if (line.is_reward_line && line.coupon_id === coupon_id) {
                points -= line.points_cost || 0;
            }
        }
        return Math.max(points, 0);
    }
});