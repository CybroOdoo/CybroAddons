/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
patch(PosStore.prototype, {
     async _processData(loadedData) {
        // To load data to pos session
        await super._processData(...arguments);
        this.res_config_settings = loadedData["res.config.settings"];
     }
});
