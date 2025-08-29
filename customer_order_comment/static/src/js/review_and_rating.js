/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CustomerReviewProduct = publicWidget.Widget.extend({
    selector: '.master',
    events: {
        'mouseover .rating-component .star': '_ReviewHover',
        'mouseout .rating-component .star': '_ReviewOut',
        'click .rating-component .stars-box .star': '_SubmitReview',
        'click .compliment-container .fa-smile-wink': '_SubmitCompliment',
        'click .feedback-tags': '_SubmitFeedBack',
    },

    _ReviewHover: function (ev) {
        const onStar = parseInt(ev.target.dataset.value, 10);
        const stars = this.el.querySelectorAll(".stars-box .star");

        stars.forEach((star, index) => {
            if (index < onStar) {
                star.classList.add("hover");
            }
        });
    },

    _ReviewOut: function () {
        const stars = this.el.querySelectorAll(".stars-box .star");

        stars.forEach(star => {
            star.classList.remove("hover");
        });
    },

    _SubmitReview: function (ev) {
        const onStar = parseInt(ev.target.dataset.value, 10);
        const stars = ev.target.closest('.stars-box').children;
        const ratingMessage = ev.target.dataset.message;

        const orderIdElement = document.getElementById('order_id');
        if (orderIdElement) {
            orderIdElement.value = document.querySelector('.monetary_field')?.dataset.oeId || '';
        }

        const rateValueElement = document.querySelector('.rating-component .star-rate .rate-value');
        if (rateValueElement) {
            rateValueElement.value = onStar;
        }

        document.querySelectorAll(".fa-smile-wink, .button-box .done").forEach(el => el.style.display = "block");

        const doneButton = document.querySelector(".button-box .done");
        if (doneButton) {
            doneButton.disabled = onStar !== 5;
        }

        Array.from(stars).forEach((star, index) => {
            if (index < onStar) {
                star.classList.add("selected");
            } else {
                star.classList.remove("selected");
            }
        });

        const statusMsg = document.querySelector(".status-msg");
        if (statusMsg) {
            const ratingMsgElement = statusMsg.querySelector(".rating_msg");
            if (ratingMsgElement) {
                ratingMsgElement.value = ratingMessage;
            }
            statusMsg.innerHTML = ratingMessage;
        }

        document.querySelectorAll("[data-tag-set]").forEach(el => el.style.display = "none");
        const tagSet = document.querySelector(`[data-tag-set="${onStar}"]`);
        if (tagSet) {
            tagSet.style.display = "block";
        }
    },

    _SubmitCompliment: function () {
        this.el.style.display = "none";
        const complimentList = document.querySelector(".list-of-compliment");
        if (complimentList) {
            complimentList.style.display = "block";
        }
    },

    _SubmitFeedBack: function (ev) {
        const tagsBox = ev.target.closest("div.tags-box");
        if (!tagsBox) return;

        let chosenTags = tagsBox.querySelectorAll("input").length + 1;

        if (ev.target.classList.contains("chosen")) {
            ev.target.classList.remove("chosen");
            chosenTags -= 2;  // Subtract 2 since we are toggling the class
        } else {
            ev.target.classList.add("chosen");
            const doneButton = document.querySelector(".button-box .done");
            if (doneButton) {
                doneButton.removeAttribute("disabled");
            }
        }

        const doneButton = document.querySelector(".button-box .done");
        if (doneButton) {
            doneButton.disabled = chosenTags <= 0;
        }
    },
});
