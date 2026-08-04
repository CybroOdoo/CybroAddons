/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    onMounted() {
        // Odoo 19 core crashes on refund orders if lines is empty when accessing lines[0]
        // We guard that access here before calling super.
        const order = this.currentOrder;
        if (order && order.isRefund && (!order.lines || order.lines.length === 0)) {
            // Skip the invoice check if there are no lines yet
            // Normal payment screen setup can continue without it
            return;
        }
        return super.onMounted(...arguments);
    },

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
        } catch (e) {
            // Don't crash the validation if loyalty point update fails
            console.warn("Could not update remaining loyalty points:", e);
        }
        return res;
    },
});
