/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.CustomerReviewProduct = publicWidget.Widget.extend({
    selector: '.master',

    events: {
        'mouseover .star': '_ReviewHover',
        'mouseout .star': '_ReviewOut',
        'click .stars-box .star': '_SubmitReview',
        'input input[name="comment"]': '_onCommentInput',
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

        const comment = this.$('input[name="comment"]').val();

        console.log("[CustomerReview] Star clicked — sending to server:", { rating: onStar, comment });

        this._saveToOrder({ rating: onStar, comment: comment || '' });
    },

    _onCommentInput() {
        clearTimeout(this._commentTimer);
        this._commentTimer = setTimeout(() => {
            const rating = this.$('.rate-value').val();
            const comment = this.$('input[name="comment"]').val();
            console.log("[CustomerReview] Comment input debounce fired:", { rating, comment });
            if (comment) {
                this._saveToOrder({ rating: rating || 0, comment });
            }
        }, 800);
    },

    _saveToOrder(payload) {
        console.log("[CustomerReview] Calling /customer/review/session with:", payload);
        return rpc("/customer/review/session", payload)
            .then((result) => {
                console.log("[CustomerReview] Server responded:", result);
            })
            .catch((err) => {
                console.error("[CustomerReview] RPC FAILED:", err);
            });
    },
});