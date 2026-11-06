/** @odoo-module **/
/**
 * Petzen "Leave a Review" form: star picker + AJAX submit to /reviews/submit
 * (creates a pending petzen.review, published on the page once approved).
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToElement } from "@web/core/utils/render";
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.PetzenReviewForm = publicWidget.Widget.extend({
    selector: ".review-form-section",
    events: {
        "click .star-pick": "_onStarClick",
        "mouseenter .star-pick": "_onStarHover",
        "mouseleave .star-pick": "_onStarLeave",
        "submit #review-form": "_onSubmit",
    },

    async willStart() {
        await this._super(...arguments);
        try {
            this.customerTypes = await rpc("/petzen/reviews/customer_types", {});
        } catch {
            this.customerTypes = [];
        }
    },

    start() {
        this._renderCustomerTypes();
        this.starVal = 5;
        this._setStars(5);
        // the success modal is a sibling of the form section in the page (views/reviews.xml)
        this.modal = this.el.closest("#wrap")?.querySelector("#review-success-modal");
        this._closeModal = this._closeModal.bind(this);
        this._onModalClick = this._onModalClick.bind(this);
        this.modal?.addEventListener("click", this._onModalClick);
        return this._super(...arguments);
    },

    destroy() {
        this.modal?.removeEventListener("click", this._onModalClick);
        // options come from the backend: never saved in the page by the website editor
        this.el.querySelector("#review-customer-type")?.replaceChildren();
        this._super(...arguments);
    },

    // reviewer type ("I am a…") ------------------------------------------------

    _renderCustomerTypes() {
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
    },

    // stars ----------------------------------------------------------------

    _onStarClick(ev) {
        this.starVal = parseInt(ev.currentTarget.dataset.v);
        this.el.querySelector("#star-val").value = this.starVal;
        this._setStars(this.starVal);
    },

    _onStarHover(ev) {
        this._setStars(parseInt(ev.currentTarget.dataset.v));
    },

    _onStarLeave() {
        this._setStars(this.starVal);
    },

    _setStars(val) {
        this.el.querySelectorAll(".star-pick").forEach((star, i) => {
            star.style.color = i < val ? "#F59E0B" : "var(--border)";
        });
    },

    // success modal ----------------------------------------------------------

    _openModal(rating) {
        if (!this.modal) {
            return;
        }
        this.modal.querySelector("#modal-stars").textContent = "★".repeat(rating);
        this.modal.classList.add("open");
        document.body.style.overflow = "hidden";
    },

    _closeModal() {
        this.modal?.classList.remove("open");
        document.body.style.overflow = "";
    },

    _onModalClick(ev) {
        if (ev.target === this.modal || ev.target.closest("#review-modal-close-btn")) {
            this._closeModal();
        }
    },

    // submit -----------------------------------------------------------------

    _setError(msg) {
        const banner = this.el.querySelector("#review-error-banner");
        if (!banner) {
            return;
        }
        banner.querySelector("#review-error-text").textContent = msg || "";
        banner.classList.toggle("visible", !!msg);
    },

    async _onSubmit(ev) {
        ev.preventDefault();
        const form = ev.currentTarget;
        const btn = form.querySelector("button[type=submit]");
        const rating = parseInt(form.querySelector("#star-val").value || this.starVal);
        const btnHtml = btn.innerHTML;
        btn.disabled = true;
        btn.textContent = _t("Submitting…");
        this._setError("");
        try {
            const result = await rpc("/reviews/submit", {
                name: form.querySelector("#review-name").value.trim(),
                email: form.querySelector("#review-email").value.trim(),
                rating: rating,
                review: form.querySelector("#review-text").value.trim(),
                customer_type: form.querySelector("#review-customer-type")?.value || "",
            });
            if (result.success) {
                form.reset();
                this._renderCustomerTypes();
                this.starVal = 5;
                form.querySelector("#star-val").value = 5;
                this._setStars(5);
                this._openModal(rating);
            } else {
                this._setError(result.error || _t("Something went wrong. Please try again."));
            }
        } catch {
            this._setError(_t("Network error. Please check your connection and try again."));
        } finally {
            btn.disabled = false;
            btn.innerHTML = btnHtml;
        }
    },
});

/**
 * Approved customer reviews (petzen.review) in the testimonials grid of the reviews
 * page. Loaded from /petzen/reviews/approved instead of being rendered in the page,
 * so the page stays fully editable: the website editor only sees (and saves) the
 * static testimonial cards. Not started in edit mode.
 */
publicWidget.registry.PetzenApprovedReviews = publicWidget.Widget.extend({
    selector: ".pz-approved-reviews",

    async willStart() {
        await this._super(...arguments);
        try {
            this.reviews = await rpc("/petzen/reviews/approved", { limit: 12 });
        } catch {
            this.reviews = [];
        }
    },

    start() {
        const cards = (this.reviews || []).map((review) =>
            renderToElement("theme_petzen.ApprovedReviewCard", { review })
        );
        // after the featured testimonial, like the design
        const featured = this.el.querySelector(":scope > .featured-testi");
        if (featured) {
            featured.after(...cards);
        } else {
            this.el.prepend(...cards);
        }
        return this._super(...arguments);
    },

    destroy() {
        this.el.querySelectorAll(":scope > .pz-approved-review").forEach((card) => card.remove());
        this._super(...arguments);
    },
});
