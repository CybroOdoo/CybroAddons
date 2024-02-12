/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

//Patching the PosStore to load the data from the model pos.custom.message
patch(PosStore.prototype, {
    //For loading the data from the model pos.custom.message
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pos_custom_message = loadedData["pos.custom.message"];
    }
});
