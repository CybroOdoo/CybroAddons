import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/**
 * Customer feedback on the payment step of the checkout: a 1 to 4 star rating
 * and a comment, saved on the cart while the customer fills them in and shown
 * again when they come back to this step.
 */
export class CustomerFeedback extends Interaction {
    static selector = ".o_textile_feedback";
    dynamicContent = {
        ".o_textile_feedback_star": {
            "t-on-mouseenter": this.onStarEnter,
            "t-on-mouseleave": this.onStarLeave,
            "t-on-click": this.onStarClick,
            "t-att-class": (el) => {
                const value = parseInt(el.dataset.value);
                return {
                    "oi-filled": value <= (this.hovered || this.rating),
                    o_textile_feedback_star_active: value <= (this.hovered || this.rating),
                };
            },
        },
        ".o_textile_feedback_status": {
            "t-out": () => this.message,
        },
        ".o_textile_feedback_comment": {
            "t-on-input": this.debounced(this.onCommentInput, 800),
        },
    };

    setup() {
        this.rating = parseInt(this.el.dataset.rating) || 0;
        this.hovered = 0;
        this.message = this.starEl?.dataset.message || "";
    }

    onStarEnter(ev) {
        this.hovered = parseInt(ev.currentTarget.dataset.value);
    }

    onStarLeave() {
        this.hovered = 0;
    }

    async onStarClick(ev) {
        this.rating = parseInt(ev.currentTarget.dataset.value);
        this.message = ev.currentTarget.dataset.message;
        await this.save({ rating: this.rating, comment: this.commentEl.value });
    }

    async onCommentInput() {
        await this.save({ comment: this.commentEl.value });
    }

    get starEl() {
        return this.el.querySelector(`.o_textile_feedback_star[data-value="${this.rating}"]`);
    }

    get commentEl() {
        return this.el.querySelector(".o_textile_feedback_comment");
    }

    async save(params) {
        await this.waitFor(rpc("/customer/review/session", params));
    }
}

registry
    .category("public.interactions")
    .add("textile_management.customer_feedback", CustomerFeedback);
