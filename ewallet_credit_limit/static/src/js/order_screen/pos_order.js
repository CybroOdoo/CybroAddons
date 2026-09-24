/** @odoo-module **/
import { Order } from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

const PosOrderLoyalty = (Order) => class PosOrderLoyalty extends Order {
    _getRealCouponPoints(coupon_id) {
        let points = 0;
        const dbCoupon = this.pos.couponCache[coupon_id];
        const matchedCard = this.pos.loyalty_card?.find((loyalty_card) => loyalty_card.id == dbCoupon?.id)
        if (matchedCard && matchedCard.set_limit) {
            points = Math.min(matchedCard.balance_limit_amount, dbCoupon.points);
        } else if (dbCoupon) {
            points = dbCoupon.points;
        }
        Object.values(this.couponPointChanges).some((pe) => {
            if (pe.coupon_id === coupon_id) {
                if (this.pos.program_by_id[pe.program_id].applies_on !== 'future') {
                    points += pe.points;
                }
                return true;
            }
            return false;
        });

        for (const line of this.get_orderlines()) {
            if (line.is_reward_line && line.coupon_id === coupon_id) {
                points -= line.points_cost;
            }
        }
        return points;
    }
}

Registries.Model.extend(Order, PosOrderLoyalty);