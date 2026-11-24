/** @odoo-module **/
/**
 * Petzen "Leave a Review" form: star picker + AJAX submit to /reviews/submit
 * (creates a pending petzen.review, published on the page once approved).
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.PetzenReviewForm = publicWidget.Widget.extend({
    selector: ".review-form-section",
    events: {
        "click .star-pick": "_onStarClick",
        "mouseenter .star-pick": "_onStarHover",
        "mouseleave .star-pick": "_onStarLeave",
        "submit #review-form": "_onSubmit",
    },

    start() {
        this.starVal = 5;
        this._setStars(5);
        this.modal = document.getElementById("review-success-modal");
        this._closeModal = this._closeModal.bind(this);
        this._onModalClick = this._onModalClick.bind(this);
        this.modal?.addEventListener("click", this._onModalClick);
        return this._super(...arguments);
    },

    destroy() {
        this.modal?.removeEventListener("click", this._onModalClick);
        this._super(...arguments);
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
        btn.textContent = "Submitting…";
        this._setError("");
        try {
            const result = await jsonrpc("/reviews/submit", {
                name: form.querySelector("#review-name").value.trim(),
                email: form.querySelector("#review-email").value.trim(),
                rating: rating,
                review: form.querySelector("#review-text").value.trim(),
            });
            if (result.success) {
                form.reset();
                this.starVal = 5;
                form.querySelector("#star-val").value = 5;
                this._setStars(5);
                this._openModal(rating);
            } else {
                this._setError(result.error || "Something went wrong. Please try again.");
            }
        } catch {
            this._setError("Network error. Please check your connection and try again.");
        } finally {
            btn.disabled = false;
            btn.innerHTML = btnHtml;
        }
    },
});

publicWidget.registry.PetzenReviews = publicWidget.Widget.extend({
    selector: ".js_petzen_reviews",

    renderToHtml(template, context = {}) {
        return renderToElement(template, context);
    },

    async start() {
        await this._super(...arguments);
        try {
            const data = await jsonrpc("/theme_petzen/get_reviews_data");
            const renderedContent = this.renderToHtml("theme_petzen.reviews_dynamic_content", {
                reviews: (data && data.reviews) || [],
            });
            if (renderedContent) {
                const existing = this.el.querySelector(".testi-layout");
                if (existing) {
                    existing.remove();
                }
                this.el.appendChild(renderedContent);
                this.el.querySelectorAll(".reveal").forEach((item) => {
                    item.classList.add("in");
                });
            }
        } catch (err) {
            // Reviews stay hidden when the request fails.
        }
    },
});
