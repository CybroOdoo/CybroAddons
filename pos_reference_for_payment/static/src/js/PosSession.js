/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
patch(PosStore.prototype, {
     async _processData(loadedData) {
        await super._processData(...arguments);
        // Load field values of in pos.payment into pos.
         this.user_payment_reference = loadedData['pos.payment'];
         // Load field values of in res.config.settings into pos.
         this.is_allow_payment_ref = loadedData['res.config.settings'];
        }
});