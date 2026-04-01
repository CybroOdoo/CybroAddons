/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async afterOrderValidation(suggestToSync = true) {
        const order = this.pos.get_order();
        const coupon = order.selectedCoupon;
        const pointsCost = order.pointsCost;

        const res = await super.afterOrderValidation(...arguments);

        if (pointsCost != undefined && coupon != undefined) {
            await this.env.services.orm.call(
                'pos.order.line', 'deduct_loyalty_points',
                [[coupon], [pointsCost], [order.access_token]]
            );
        }
        return res;
    },
});
