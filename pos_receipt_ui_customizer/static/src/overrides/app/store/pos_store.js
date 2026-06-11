/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async _save_to_server(orders, options) {
        const result = await super._save_to_server(...arguments);
        if (result && Array.isArray(result)) {
            for (const orderData of result) {
                if (orderData.custom_qr_image) {
                    const order = this.orders.find(o => o.name === orderData.pos_reference);
                    if (order) {
                        order.custom_qr_image = orderData.custom_qr_image;
                        order.custom_receipt_token = orderData.custom_receipt_token;
                    }
                }
            }
        }
        return result;
    }
});