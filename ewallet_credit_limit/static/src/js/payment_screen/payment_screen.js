/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    },
    async validateOrder(isForceValidate) {
        const order = this.pos?.get_order();
        await super.validateOrder(...arguments);
        let points = 0;
        const orderLinesData = (order.lines || []).map(line => ({
            coupon_id: line.coupon_id?.id || false,
            point_cost: line.points_cost || 0,
        })).filter(line => line.coupon_id);
        if (orderLinesData.length > 0) {
          try {
                const result = await this.orm.call(
                    'pos.order',
                    'set_remaining_balance',
                    [orderLinesData],
                    {}
                );
                if (!result) {
                    console.warn('Failed to process order and update coupon balance');
                }
            } catch (error) {
                console.error('ORM Error in action_post_order:', error);
            }
        }
        return Math.max(0, points);
    },
});
