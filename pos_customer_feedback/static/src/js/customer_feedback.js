/** @odoo-module **/
/**
 * Defines CustomerFeedback which extends PosComponent
 *
 */
import PosComponent from 'point_of_sale.PosComponent';
import ProductScreen from "point_of_sale.ProductScreen";
import Registries from "point_of_sale.Registries";
import { useListener } from "@web/core/utils/hooks";
import { useRef, onMounted } from "@odoo/owl"

class CustomerFeedback extends PosComponent {
    /**
     * Performs setup tasks for the CustomerFeedback component.
     */
    setup() {
        super.setup();
        useListener('click', this.onClick);
        this.feedback_Customer = useRef('input-data')
        onMounted(()=>{
            const starValue = this.env.pos.selectedOrder.customer_feedback
            if (starValue){
                this.setStarRating(starValue);
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
        let partner = this.env.pos.get_order().get_partner();
        let selectedOrderline = this.env.pos.get_order().get_selected_orderline();
        if (!partner || !selectedOrderline) return;

        const { confirmed, payload: inputFeedback } = await this.showPopup(
        'FeedbackPopup', {
            startingValue: this.env.pos.get_order().get_comment_feedback(),
            title: this.env._t('Customer Feedback'),
        });

        if (confirmed) {
            this.env.pos.selectedOrder.comment_feedback = inputFeedback.commentValue;
            this.env.pos.selectedOrder.customer_feedback = inputFeedback.ratingValue;
            this.setStarRating(inputFeedback.ratingValue)
        }
    }
}
CustomerFeedback.template = 'CustomerFeedback';
ProductScreen.addControlButton({
    component: CustomerFeedback,
});
Registries.Component.add(CustomerFeedback);
return CustomerFeedback;
