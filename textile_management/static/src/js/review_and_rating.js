/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.CustomerReviewProduct = publicWidget.Widget.extend({
    selector: '.master',

    events: {
        'mouseover .star': '_ReviewHover',
        'mouseout .star': '_ReviewOut',
        'click .stars-box .star': '_SubmitReview',
        'blur input[name="comment"]': '_saveCommentToSession',
    },

    _ReviewHover(ev) {
        const onStar = parseInt(ev.target.dataset.value, 10);
        this.el.querySelectorAll(".star").forEach((star, i) => {
            star.classList.toggle("hover", i < onStar);
        });
    },

    _ReviewOut() {
        this.el.querySelectorAll(".star").forEach(s => s.classList.remove("hover"));
    },

    _SubmitReview(ev) {
        const onStar = parseInt(ev.target.dataset.value, 10);
        const message = ev.target.dataset.message;

        this.el.querySelectorAll(".star").forEach((star, i) => {
            star.classList.toggle("selected", i < onStar);
        });

        this.$('.rate-value').val(onStar);
        this.$('.rating_msg').val(message);
        this.$('.status-msg').text(message);

        rpc("/customer/review/session", { rating: onStar });
    },

    _saveCommentToSession() {
        const rating = this.$('.rate-value').val();
        const comment = this.$('input[name="comment"]').val();
        if (!rating || !comment) return;

        rpc("/customer/review/session", {
            rating: rating,
            comment: comment,
        });
    },
});
