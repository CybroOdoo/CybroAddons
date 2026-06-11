/** @odoo-module **/
/**
 * Extends PosStore and it extends Registries
 * Override the _processData method to process loaded data
 **/
import {patch} from "@web/core/utils/patch";
import {PosStore} from "@point_of_sale/app/store/pos_store";
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.res_config_settings = loadedData['res.config.settings'];
    }
});