/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
       async processServerData() {
          super.processServerData(...arguments);
        this.pos_orders = this.data.models['pos.order'].getFirst();
        this.pos_order_lines = this.data.models['pos.order.line'].getAll()
       }
});
