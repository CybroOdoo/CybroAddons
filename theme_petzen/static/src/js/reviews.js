/**
 * Petzen reviews page:
 *  - "Leave a Review" form: star picker + submit to /reviews/submit (creates a
 *    pending petzen.review, published on the page once approved);
 *  - approved reviews added to the testimonials grid.
 */
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const STAR_ON = "#F59E0B";
const STAR_OFF = "var(--border)";

export class PetzenReviewForm extends Interaction {
    static selector = ".review-form-section";
    dynamicContent = {
        ".star-pick": {
            "t-on-click": this.onStarClick,
            "t-on-mouseenter": this.onStarHover,
            "t-on-mouseleave": this.onStarLeave,
        },
        "#review-form": { "t-on-submit.prevent.withTarget": this.locked(this.onSubmit) },
    };

    setup() {
        this.starVal = 5;
        // success modal: rendered after #wrap, outside the editable area
        this.modal = this.el.ownerDocument.querySelector("#review-success-modal");
    }

    async willStart() {
        try {
            this.customerTypes = await this.waitFor(rpc("/petzen/reviews/customer_types", {}));
        } catch {
            this.customerTypes = [];
        }
    }

    start() {
        this.renderCustomerTypes();
        this.setStars(this.starVal);
        if (this.modal) {
            this.addListener(this.modal, "click", this.onModalClick);
        }
        // the options come from the backend: never saved in the page by the editor
        this.registerCleanup(() => this.el.querySelector("#review-customer-type")?.replaceChildren());
    }

    // reviewer type ("I am a…") ---------------------------------------------

    /**
     * Fill the "I am a…" select with the reviewer types of petzen.review.
     */
    renderCustomerTypes() {
        const select = this.el.querySelector("#review-customer-type");
        if (!select) {
            return;
        }
        select.replaceChildren(...(this.customerTypes || []).map(({ value, label }) => {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = label;
            option.selected = value === "verified";
            return option;
        }));
        select.closest(".booking-field")?.classList.toggle("d-none", !select.options.length);
    }

    // stars -------------------------------------------------------------------

    /**
     * @param {MouseEvent} ev
     */
    onStarClick(ev) {
        this.starVal = parseInt(ev.currentTarget.dataset.v);
        this.el.querySelector("#star-val").value = this.starVal;
        this.setStars(this.starVal);
    }

    /**
     * @param {MouseEvent} ev
     */
    onStarHover(ev) {
        this.setStars(parseInt(ev.currentTarget.dataset.v));
    }

    onStarLeave() {
        this.setStars(this.starVal);
    }

    /**
     * Color the first `val` stars of the picker.
     *
     * @param {number} val
     */
    setStars(val) {
        this.el.querySelectorAll(".star-pick").forEach((star, i) => {
            star.style.color = i < val ? STAR_ON : STAR_OFF;
        });
    }

    // success modal -----------------------------------------------------------

    /**
     * @param {number} rating
     */
    openModal(rating) {
        if (!this.modal) {
            return;
        }
        this.modal.querySelector("#modal-stars").textContent = "★".repeat(rating);
        this.modal.classList.add("open");
        this.el.ownerDocument.body.style.overflow = "hidden";
    }

    closeModal() {
        this.modal?.classList.remove("open");
        this.el.ownerDocument.body.style.overflow = "";
    }

    /**
     * Close the modal on the overlay or on its close button.
     *
     * @param {MouseEvent} ev
     */
    onModalClick(ev) {
        if (ev.target === this.modal || ev.target.closest("#review-modal-close-btn")) {
            this.closeModal();
        }
    }

    // submit ------------------------------------------------------------------

    /**
     * @param {string} msg error message, empty to hide the banner
     */
    setError(msg) {
        const banner = this.el.querySelector("#review-error-banner");
        if (!banner) {
            return;
        }
        banner.querySelector("#review-error-text").textContent = msg || "";
        banner.classList.toggle("visible", !!msg);
    }

    /**
     * Send the review to /reviews/submit.
     *
     * @param {SubmitEvent} ev
     * @param {HTMLFormElement} form
     */
    async onSubmit(ev, form) {
        const btn = form.querySelector("button[type=submit]");
        const rating = parseInt(form.querySelector("#star-val").value || this.starVal);
        const btnHtml = btn.innerHTML;
        btn.disabled = true;
        btn.textContent = _t("Submitting…");
        this.setError("");
        try {
            const result = await this.waitFor(rpc("/reviews/submit", {
                name: form.querySelector("#review-name").value.trim(),
                email: form.querySelector("#review-email").value.trim(),
                rating: rating,
                review: form.querySelector("#review-text").value.trim(),
                customer_type: form.querySelector("#review-customer-type")?.value || "",
                website_url: form.querySelector("#review-website-url")?.value || "",
            }));
            if (result.success) {
                form.reset();
                this.renderCustomerTypes();
                this.starVal = 5;
                form.querySelector("#star-val").value = 5;
                this.setStars(5);
                this.openModal(rating);
            } else {
                this.setError(result.error || _t("Something went wrong. Please try again."));
            }
        } catch {
            this.setError(_t("Network error. Please check your connection and try again."));
        } finally {
            btn.disabled = false;
            btn.innerHTML = btnHtml;
        }
    }
}

/**
 * Approved customer reviews (petzen.review) in the testimonials grid of the
 * reviews page. Loaded from /petzen/reviews/approved instead of being rendered
 * in the page, so the page stays fully editable: the website editor only sees
 * (and saves) the static testimonial cards. Not started in edit mode.
 */
export class PetzenApprovedReviews extends Interaction {
    static selector = ".pz-approved-reviews";

    async willStart() {
        try {
            this.reviews = await this.waitFor(rpc("/petzen/reviews/approved", { limit: 12 }));
        } catch {
            this.reviews = [];
        }
    }

    start() {
        // after the featured testimonial, like the design (removed when stopped)
        let anchor = this.el.querySelector(":scope > .featured-testi");
        const reviews = anchor ? this.reviews || [] : [...(this.reviews || [])].reverse();
        for (const review of reviews) {
            const [card] = anchor
                ? this.renderAt("theme_petzen.ApprovedReviewCard", { review }, anchor, "afterend")
                : this.renderAt("theme_petzen.ApprovedReviewCard", { review }, this.el, "afterbegin");
            if (anchor) {
                anchor = card;
            }
        }
    }
}

registry.category("public.interactions").add("theme_petzen.review_form", PetzenReviewForm);
registry.category("public.interactions").add("theme_petzen.approved_reviews", PetzenApprovedReviews);
