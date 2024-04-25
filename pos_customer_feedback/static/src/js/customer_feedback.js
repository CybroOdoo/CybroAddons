odoo.define('pos_customer_feedback.CustomerFeedback', function (require) {
    'use strict';
    /**
     * Defines CustomerFeedback which extends PosComponent
     *
     */
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { onMounted , useRef } = owl.hooks;
    const { _t } = require('web.core');

    class CustomerFeedback extends PosComponent {
    /**
     * Performs setup tasks for the CustomerFeedback component.
     */
        setup() {
        super.setup();
        useListener('click', this.onClick);
        this.feedback_Customer = useRef('input-data')
        onMounted(()=>{
                if(this.env.pos.selectedOrder){
                    this.starValue = this.env.pos.selectedOrder.customer_feedback
                    if (starValue){
                        this.setStarRating(starValue);
                    }
                }
            })
        }
        /**
         * Sets the star rating based on the provided value.
         *
         * @param {number} starValue - The value representing the star rating.
         */
        setStarRating(starValue){
            let newStarValue = starValue || 0;
            const starPercentage = (parseInt(newStarValue)/ 5) * 100;
            const starPercentageRounded = `${(Math.round(starPercentage / 10) * 10)}%`;
            document.querySelector(`.stars-inner`).style.width =starPercentageRounded
        }
        /**
         * Handles the click event when the feedback component is clicked.
         *
         * @param {Event} ev - The click event object.
         */
        async onClick(ev) {
        let order =this.env.pos.get_order()
        let partner = order.attributes.client;
        let selectedOrderline = order.get_selected_orderline();
        if (!partner || !selectedOrderline) return;
        const { confirmed, payload: inputFeedback } = await this.showPopup(
        'FeedbackPopup', {
            startingValue: order.get_comment_feedback(),
            ratingValue: order.get_customer_feedback(),
            title: this.env._t('Customer Feedback'),
        });
        if (confirmed) {
                order.comment_feedback = inputFeedback.commentValue;
                order.customer_feedback = inputFeedback.ratingValue;
                this.setStarRating(inputFeedback.ratingValue)
            }
        }
    }
    CustomerFeedback.template = 'pos_customer_feedback.CustomerFeedback';

    ProductScreen.addControlButton({
        component: CustomerFeedback,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(CustomerFeedback);

    return CustomerFeedback;
});
