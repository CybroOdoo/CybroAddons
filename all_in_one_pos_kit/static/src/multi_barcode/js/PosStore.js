/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async _processData(loadedData) {
     //@override
        await super._processData(...arguments);
        this.product_by_lot = loadedData['multi.barcode.products'];
        this.product_by_lot_id = loadedData['multi_barcode'];
    }
});
