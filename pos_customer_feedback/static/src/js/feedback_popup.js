/** @odoo-module **/
/**
 * Defines AbstractAwaitablePopup extending from AbstractAwaitablePopup
 */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _lt } from '@web/core/l10n/translation';
import  { onMounted, useRef, useState } from "@odoo/owl";

class FeedbackPopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
        this.state = useState({
            ratingValue: '',
            commentValue: this.props.startingValue
        });
        this.CommentRef = useRef('comment');
        onMounted(this.onMounted);
    }
    onMounted() {
        this.CommentRef.el.focus();
    }
    async RatingChange(ev) {
        if (!isNaN(parseInt(ev.target.value))) {
            this.state.ratingValue = ev.target.value;
            const starTotal = 5;
            const starPercentage = (this.state.ratingValue / starTotal) * 100;
            const starPercentageRounded = `${(Math.round(starPercentage / 10) * 10)}%`;
            document.querySelector(`.stars-inner`).style.width = starPercentageRounded;
        }
    }
    getPayload() {
        return {
            ratingValue: this.state.ratingValue,
            commentValue: this.state.commentValue,
        };
    }
}
FeedbackPopup.template = 'FeedbackPopup';
FeedbackPopup.defaultProps = {
    confirmText: _lt('Ok'),
    cancelText: _lt('Cancel'),
    title: '',
    body: '',
};
export default FeedbackPopup;
