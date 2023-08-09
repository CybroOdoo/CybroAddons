/** @odoo-module **/
/**
 * Defines AbstractAwaitablePopup extending from AbstractAwaitablePopup
 */
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
import Registries from 'point_of_sale.Registries';
import { _lt } from '@web/core/l10n/translation';
import  { onMounted, useRef, useState } from "@odoo/owl";

class FeedbackPopup extends AbstractAwaitablePopup {
    /**
     * @param {Object} props
     * @param {string} props.startingValue
     */
    setup() {
        super.setup();
        this.state = useState({
        ratingValue:'',
        commentValue: this.props.startingValue
        });
        this.CommentRef = useRef('comment')
        onMounted(this.onMounted);
    }
    /**
     * Called after the component is mounted.
     * Sets focus on the comment input field.
     */
    onMounted() {
        this.CommentRef.el.focus();
    }
    /**
     * Handles the change event of the rating input field.
     * Updates the rating value and adjusts the star percentage accordingly.
     *
     * @param {Event} ev - The change event object.
     */
    async RatingChange(ev) {
        if(!isNaN(parseInt(ev.target.value))){
            this.state.ratingValue=ev.target.value;
            const starTotal = 5;
            const starPercentage = (this.state.ratingValue/ starTotal) * 100;
            const starPercentageRounded = `${(Math.round(starPercentage / 10) * 10)}%`;
            document.querySelector(`.stars-inner`).style.width = starPercentageRounded;
        }
    }
    /**
     * Retrieves the payload data to be returned when the popup is confirmed.
     *
     * @returns {Object} The payload data containing the ratingValue and commentValue.
     */
    getPayload() {
        return {
            ratingValue : this.state.ratingValue,
            commentValue: this.state.commentValue,
        }
    }
}
FeedbackPopup.template = 'FeedbackPopup';
FeedbackPopup.defaultProps = {
    confirmText: _lt('Ok'),
    cancelText: _lt('Cancel'),
    title: '',
    body: '',
};
Registries.Component.add(FeedbackPopup);
return FeedbackPopup;
