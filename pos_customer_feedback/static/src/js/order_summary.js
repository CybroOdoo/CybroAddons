/** @odoo-module **/
/**
 * Defines CustFeedback which extends Order from point of sale models
 *
 * Initialize the additional properties from JSON and export the additional properties as JSON
 */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    constructor() {
        this.customer_feedback = this.customer_feedback || null;
        this.comment_feedback = this.comment_feedback || null;
        this._super(...arguments);
    },
    set_comment_feedback(comment_feedback) {
        this.comment_feedback = comment_feedback.commentValue;
        this.customer_feedback = comment_feedback.ratingValue;
    },
    get_comment_feedback() {
        return this.comment_feedback;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.customer_feedback = this.customer_feedback;
        json.comment_feedback = this.comment_feedback;
        return json;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.customer_feedback = json.customer_feedback;
        this.comment_feedback = json.comment_feedback;
    },
});
