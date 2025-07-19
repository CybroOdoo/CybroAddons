/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
       async processServerData() {
          super.processServerData(...arguments);
        this.order_questions = this.data.models['pos.order.question'].getAll()
       }
});