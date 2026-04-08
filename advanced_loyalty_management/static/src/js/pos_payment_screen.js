/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async afterOrderValidation(suggestToSync = true) {
        const order = this.pos.get_order();
        const rewardCouponIds = [
            ...new Set(
                (order?._get_reward_lines?.() || [])
                    .filter((line) => line.coupon_id)
                    .map((line) => line.coupon_id)
            ),
        ];

        const res = await super.afterOrderValidation(...arguments);

        if (rewardCouponIds.length) {
            const remainingPoints = await this.env.services.orm.call(
                'pos.order.line', 'deduct_loyalty_points',
                [[], [], [order.access_token]]
            );
            for (const couponId of rewardCouponIds) {
                const currentCoupon = this.pos.couponCache[couponId];
                const updatedBalance = remainingPoints?.[couponId];
                if (currentCoupon && updatedBalance !== undefined) {
                    currentCoupon.balance = updatedBalance;
                }
            }
        }
        return res;
    },
});
