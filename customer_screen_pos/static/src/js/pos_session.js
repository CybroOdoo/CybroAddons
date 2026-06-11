/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
       async processServerData(data) {
          super.processServerData(...arguments);
        this.res_setting = this.data.models['res.config.settings'].getFirst();
       }
})