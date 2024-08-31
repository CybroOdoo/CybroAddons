/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";


patch(PosStore.prototype, {
    // @Override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pos_orders = loadedData['pos.order'];
        this.pos_order_lines = loadedData['pos.order.line'];
    },
});
