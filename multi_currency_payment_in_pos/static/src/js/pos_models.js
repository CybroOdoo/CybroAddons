/** @odoo-module */
/** Loading all currencies and its parameters.*/
import { registry } from "@web/core/registry";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
patch(PosStore.prototype, {
    async _processData(loadedData) {
 await super._processData(...arguments);
 this.your_model = loadedData['res.currency'];

 }
})