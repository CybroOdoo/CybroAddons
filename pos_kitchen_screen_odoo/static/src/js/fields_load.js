/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    /**
     * Processes loaded data for the Point of Sale store.
     *
     * @param {Object} loadedData - The data loaded for the Point of Sale.
     * @returns {Promise} A promise that resolves when the data is processed.
     */
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pos_orders = loadedData['pos.order'];
        this.pos_order_lines = loadedData['pos.order.line'];
    },

    createNewOrder() {
        const order = super.createNewOrder(...arguments);
        return order
        }
});


