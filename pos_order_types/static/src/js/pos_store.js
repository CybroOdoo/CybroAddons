/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async _processData(loadedData) {
    await super._processData(...arguments);
    this.delivery_type = loadedData['delivery.type'];
    this.type_by_id = loadedData['type_by_id'];
    },
});
