/** @odoo-module **/
// Customer feedback button fn
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { onMounted } from "@odoo/owl";
import FeedbackPopup from "@pos_customer_feedback/js/feedback_popup"
export class CustomerFeedback extends Component {
    static template = "point_of_sale.CustomerFeedback";
    setup() {
        const pos = useService("pos");
        if (!pos) {
            console.error("POS service not available");
            return;
        }
        this.pos=pos
         this.partner = pos.get_order().get_partner();
         this.selectedOrderline = pos.get_order().get_selected_orderline();

        const { popup } = this.env.services;
        this.popup = popup;

        onMounted(() => {
            const starValue = pos.selectedOrder && pos.selectedOrder.customer_feedback;
            if (starValue) {
                this.setStarRating(starValue);
            }
        });
    }

    setStarRating(starValue) {
        let newStarValue = starValue || 0;
        const starPercentage = (parseInt(newStarValue) / 5) * 100;
        const starPercentageRounded = `${(Math.round(starPercentage / 10) * 10)}%`;
        document.querySelector(`.stars-inner`).style.width = starPercentageRounded;
    }

    async onClick() {
        if (this.pos.selectedOrder.partner && this.pos.selectedOrder.orderlines){
        const { confirmed, payload: inputFeedback } = await this.popup.add(
            FeedbackPopup, {
                startingValue: this.pos.get_order().get_comment_feedback(),
                title: _t('Customer Feedback')
            }
        );
        if (confirmed) {
            this.pos.selectedOrder.comment_feedback = inputFeedback.commentValue;
            this.pos.selectedOrder.customer_feedback = inputFeedback.ratingValue;
            this.setStarRating(inputFeedback.ratingValue)
        }
    }
    }
}
ProductScreen.addControlButton({
    component: CustomerFeedback,
});
