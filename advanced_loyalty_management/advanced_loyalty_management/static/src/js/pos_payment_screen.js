/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async afterOrderValidation(suggestToSync = true) {
        const order = this.pos.get_order();
        const hasRewardLines = order?._get_reward_lines?.().some(
            (line) => line.coupon_id
        );

        const res = await super.afterOrderValidation(...arguments);

        if (hasRewardLines) {
            await this.env.services.orm.call(
                'pos.order.line', 'deduct_loyalty_points',
                [[], [], [order.access_token]]
            );
        }
        return res;
    },
});
