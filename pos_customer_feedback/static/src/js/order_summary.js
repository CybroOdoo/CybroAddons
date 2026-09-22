/** @odoo-module **/
/**
 * Defines CustFeedback which extends Order from point of sale models
 *
 * Initialize the additional properties from JSON and export the additional properties as JSON
 */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.customer_feedback = this.customer_feedback || null;
        this.comment_feedback = this.comment_feedback || null;
    },
    set_comment_feedback(comment_feedback) {
        this.comment_feedback = comment_feedback.commentValue;
        this.customer_feedback = comment_feedback.ratingValue;
    },
    get_comment_feedback() {
        return this.comment_feedback;
    },
    getSerializableFields() {
        return {
            ...super.getSerializableFields(),
            customer_feedback: { type: "number", optional: true },
            comment_feedback: { type: "string", optional: true },
        };
    },
});
