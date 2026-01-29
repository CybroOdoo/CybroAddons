odoo.define('pos_customer_feedback.CustFeedback', function (require) {
    "use strict";
    /**
     * Defines CustFeedback which extends Order from point of sale models
     *
     * Initialize the additional properties from JSON and export the additional
     properties as JSON
     */
    var models = require('point_of_sale.models');
    const { Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const _super_order = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function () {
            _super_order.initialize.apply(this, arguments);
            this.customer_feedback = this.customer_feedback || null;
            this.comment_feedback = this.comment_feedback || null;
        },
        /**
         * Sets the comment and customer feedback values.
         *
         * @param {Object} comment_feedback - Object containing the comment and
         rating values.
         */
        set_comment_feedback: function(comment_feedback){
            this.comment_feedback = comment_feedback.commentValue
            this.customer_feedback = comment_feedback.ratingValue
        },
        /**
         * Returns the comment feedback value.
         *
         * @returns {string|null} - The comment feedback value.
         */
        get_comment_feedback: function(){
            return this.comment_feedback
        },
        get_customer_feedback: function(){
            return this.customer_feedback
        },
        /**
         * Exports the CustFeedback properties as JSON.
         *
         * @returns {Object} - The CustFeedback properties as JSON.
         */
         export_as_JSON: function() {
            const json = _super_order.export_as_JSON.apply(this, arguments);
            json.customer_feedback = this.customer_feedback ;
            json.comment_feedback = this.comment_feedback;
            return json;
        },
        /**
         * Initializes the CustFeedback properties from JSON.
         *
         * @param {Object} json - The JSON object containing the CustFeedback properties.
         */
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            this.customer_feedback = json.customer_feedback;
            this.comment_feedback = json.comment_feedback;
         },
    });
});
