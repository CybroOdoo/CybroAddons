/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

patch(PosOrder.prototype, {
    setup() {
        super.setup(...arguments);
    },

    // Capture question lists from each order line before sending order data
    export_for_printing(baseUrl, headerData) {
        const data = super.export_for_printing(...arguments);
        data.question_lists = this.getAllQuestionLists();
        return data;
    },

    // Extract all QuestionLists from order lines
    getAllQuestionLists() {
        return this.lines.map(line => ({
            id: line.id,
            name:line.full_product_name,
            questions: line.question_list,
        }));
    },
});