/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";


patch(PosStore.prototype, {
    /**
    load customer tag data to PosGlobalState
    **/
    async _processData(loadedData) {
        await super._processData(loadedData);
        this.customer_tag = loadedData['res.partner.category'];
    },
});
