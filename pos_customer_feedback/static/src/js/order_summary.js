/** @odoo-module **/
/**
 * Defines CustFeedback which extends Order from point of sale models
 *
 * Initialize the additional properties from JSON and export the additional
 properties as JSON
 */
import models from 'point_of_sale.models';
import { Order } from 'point_of_sale.models';
import  Registries from "point_of_sale.Registries";
const CustFeedback = (Order) => class CustFeedback extends Order {
    /**
     * Initializes the CustFeedback class.
     */
    constructor() {
        super(...arguments);
        this.customer_feedback = this.customer_feedback || null;
        this.comment_feedback = this.comment_feedback || null;
    }
    /**
     * Sets the comment and customer feedback values.
     *
     * @param {Object} comment_feedback - Object containing the comment and
     rating values.
     */
    set_comment_feedback(comment_feedback){
        this.comment_feedback = comment_feedback.commentValue
        this.customer_feedback = comment_feedback.ratingValue
    }
     /**
     * Returns the comment feedback value.
     *
     * @returns {string|null} - The comment feedback value.
     */
    get_comment_feedback(){
    return this.comment_feedback
    }
    /**
     * Exports the CustFeedback properties as JSON.
     *
     * @returns {Object} - The CustFeedback properties as JSON.
     */
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments)
        json.customer_feedback = this.customer_feedback ;
        json.comment_feedback = this.comment_feedback
        return json;
    }
    /**
     * Initializes the CustFeedback properties from JSON.
     *
     * @param {Object} json - The JSON object containing the CustFeedback properties.
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.customer_feedback = json.customer_feedback;
        this.comment_feedback = json.comment_feedback;
     }
    };
Registries.Model.extend(Order, CustFeedback);
