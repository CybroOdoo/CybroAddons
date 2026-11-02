/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async afterOrderValidation(suggestToSync = true) {
        //---remaining points calculated after claiming the reward is shown in the redemption history
        const res = await super.afterOrderValidation(...arguments);
        try {
            const order = this.currentOrder;
            if (order && order.pointsCost !== undefined) {
                const couponId = order.selectedCoupon;
                let pointsOfPartner = 0;
                const loyaltyCard = this.pos.models["loyalty.card"].get(couponId);
                if (loyaltyCard) {
                    pointsOfPartner = loyaltyCard.points;
                }
                const pointsWon = order.uiState?.couponPointChanges?.[couponId]?.points || 0;
                const pointsSpent = order.pointsCost;
                const balance = pointsOfPartner + pointsWon - pointsSpent;
                const token = order.uuid;
                this.pos.data.call('pos.order.line', 'remaining_points', [[balance], [token]]);
            }
        } catch {
            // Don't crash the validation if loyalty point update fails
        }
        return res;
    },
});
