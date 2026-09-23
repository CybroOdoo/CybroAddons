/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    async validateOrder(args = {}) {
        const order = args.order || this.getOrder();
        const res = await super.validateOrder(...arguments);

        if (res && order && this.config?.display_stock_setting) {
            const lines = order.getOrderlines ? order.getOrderlines() : (order.lines || []);
            for (const line of lines) {
                const product = line.product_id || line.product;
                const qty = line.qty ?? line.get_quantity?.() ?? 0;
                if (product && typeof product.qty_available === "number") {
                    product.qty_available -= qty;
                }
            }
        }
        return res;
    },
});
