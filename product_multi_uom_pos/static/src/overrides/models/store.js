/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    // @Override
    async processServerData(loadedData) {
        await super.processServerData(...arguments);
        this.pos_multi_uom = this.data?.["pos.multi.uom"] || [];
    },
});
