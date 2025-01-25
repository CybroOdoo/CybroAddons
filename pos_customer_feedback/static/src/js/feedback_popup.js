/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import  { Component, onMounted, useRef, useState } from "@odoo/owl";

/* Extending Component and creating FeedbackPopup */
export class FeedbackPopup extends Component {
    static template = "point_of_sale.FeedbackPopup";
    static components = { Dialog };
    static defaultProps = {
        confirmText: _t('Ok'),
        cancelText: _t('Cancel'),
        title: '',
        body: '',
    };

    setup() {
        super.setup();
        this.state = useState({
            ratingValue: this.props.startingRating,
            commentValue: this.props.startingComment
        });
        this.CommentRef = useRef('comment');
        onMounted(this.onMounted);
    }
    onMounted() {
        this.CommentRef.el.focus();
    }
    /* Function for calculating the star rating */
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
        this.props.pos.get_order().comment = this.state.commentValue;
        this.props.pos.get_order().feedback = this.state.ratingValue;
    }

    confirm() {
        this.props.close(this.getPayload());
    }

    cancel() {
        this.props.close();
    }
}
