/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
patch(PosStore.prototype, {
    async processServerData(loadedData) {
     //@override
        await super.processServerData(...arguments);
    this['product_by_lot'] = this.data.models['multi.barcode.products']
    }
});
