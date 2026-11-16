/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";

// Patch the PosOrderline to store the QuestionList in the order line state
patch(PosOrderline.prototype, {
    setup(vals) {
        super.setup(...arguments);
        // question_list will be initialized by the RecordStore if it's in the vals.
        // We only need the getter OrderQuestion for display.
    },

    get OrderQuestion() {
        return this.question_list ? this.question_list.split(',').join('/') : '';
    },

    // Method to update the QuestionList state dynamically
    setQuestionList(questions) {
        this.update({ question_list: questions.join(',') });
        // Force synchronization by triggering update on the order
        if (this.order_id) {
            this.models["pos.order"].triggerEvents("update", { id: this.order_id.id });
        }
    },

});
