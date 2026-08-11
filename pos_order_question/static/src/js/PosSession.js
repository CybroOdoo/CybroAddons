/** @odoo-module */
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async processServerData(...args) {
        await super.processServerData(...args);
        if (this.models && this.models['pos.order.question']) {
            this.order_questions = this.models['pos.order.question'].getAll();
        } else {
            this.order_questions = [];
        }
    },
});
