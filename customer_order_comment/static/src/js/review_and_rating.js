import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class CustomerOrderCommentInteraction extends Interaction {
    static selector = ".o_customer_order_comment_wrapper";

    dynamicContent = {
        ".stars-box .star": {
            "t-on-mouseenter": this.onStarHover,
            "t-on-mouseleave": this.onStarUnhover,
            "t-on-click": this.onStarClick,
        },
        'input[name="comment"]': {
            "t-on-input": this.onCommentInput,
        },
        "form": {
            "t-on-submit": this.onFormSubmit,
        },
    };

    setup() {
        this.selectedRating = 0;
    }

    onStarHover(ev) {
        const hoveredStar = ev.currentTarget;
        const val = parseInt(hoveredStar.dataset.value, 10);
        const stars = this.el.querySelectorAll(".stars-box .star");
        stars.forEach((s) => {
            const sVal = parseInt(s.dataset.value, 10);
            if (sVal <= val) {
                s.classList.add("hover");
            } else {
                s.classList.remove("hover");
            }
        });
    }

    onStarUnhover() {
        const stars = this.el.querySelectorAll(".stars-box .star");
        stars.forEach((s) => s.classList.remove("hover"));
    }

    onStarClick(ev) {
        const star = ev.currentTarget;
        const onStar = parseInt(star.dataset.value, 10);
        const ratingMessage = star.dataset.message || "";
        this.selectedRating = onStar;

        // 1. Highlight selected stars
        const stars = this.el.querySelectorAll(".stars-box .star");
        stars.forEach((s) => {
            const sVal = parseInt(s.dataset.value, 10);
            if (sVal <= onStar) {
                s.classList.add("selected");
            } else {
                s.classList.remove("selected");
            }
        });

        // 2. Update hidden rate-value input
        const rateInputs = this.el.querySelectorAll('input[name="rate_value"], .rate-value');
        rateInputs.forEach((input) => {
            input.value = onStar;
            input.setAttribute("value", onStar);
        });

        // 3. Update status message
        const statusMsg = this.el.querySelector(".status-msg");
        if (statusMsg) {
            const ratingMsgInput = statusMsg.querySelector(".rating_msg");
            if (ratingMsgInput) {
                ratingMsgInput.value = ratingMessage;
            }
            let label = statusMsg.querySelector(".status_title");
            if (!label) {
                label = document.createElement("span");
                label.className = "status_title fw-bold text-secondary mb-2 d-block";
                statusMsg.appendChild(label);
            }
            label.textContent = ratingMessage;
        }

        // 4. Show corresponding question tag
        this.el.querySelectorAll("[data-tag-set]").forEach((el) => {
            el.style.display = "none";
        });
        const tagSet = this.el.querySelector(`[data-tag-set="${onStar}"]`);
        if (tagSet) {
            tagSet.style.display = "block";
        }

        // 5. Enable the submit button
        const doneBtn = this.el.querySelector(".button-box .done");
        if (doneBtn) {
            doneBtn.removeAttribute("disabled");
            doneBtn.disabled = false;
        }
    }

    onCommentInput(ev) {
        const doneBtn = this.el.querySelector(".button-box .done");
        if (doneBtn) {
            const hasComment = ev.target.value.trim().length > 0;
            if (hasComment || this.selectedRating > 0) {
                doneBtn.removeAttribute("disabled");
                doneBtn.disabled = false;
            }
        }
    }

    onFormSubmit() {
        if (this.selectedRating > 0) {
            const rateInputs = this.el.querySelectorAll('input[name="rate_value"], .rate-value');
            rateInputs.forEach((input) => {
                input.value = this.selectedRating;
                input.setAttribute("value", this.selectedRating);
            });
        }
    }
}

registry
    .category("public.interactions")
    .add("customer_order_comment.review_and_rating", CustomerOrderCommentInteraction);
