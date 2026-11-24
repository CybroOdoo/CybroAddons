/** @odoo-module **/
/**
 * Petzen contact page: AJAX submit of #contact-form to /contact/submit (creates a
 * crm.lead) + the "Quick Answers" FAQ accordion.
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.PetzenContactForm = publicWidget.Widget.extend({
    selector: ".pz-page-contact",
    events: {
        "submit #contact-form": "_onSubmit",
        "click #ct-reset-btn": "_onReset",
        "click .ct-faq-q": "_onFaqClick",
    },

    start() {
        this.form = this.el.querySelector("#contact-form");
        this.btn = this.el.querySelector("#ct-submit-btn");
        this.btnHtml = this.btn?.innerHTML;
        return this._super(...arguments);
    },

    _val(id) {
        const el = this.el.querySelector("#" + id);
        return el ? el.value.trim() : "";
    },

    _setError(msg) {
        const banner = this.el.querySelector("#ct-error-banner");
        if (banner) {
            banner.querySelector("#ct-error-text").textContent = msg || "";
            banner.style.display = msg ? "flex" : "none";
        }
    },

    async _onSubmit(ev) {
        ev.preventDefault();
        this._setError("");
        this.btn.disabled = true;
        this.btn.textContent = "Sending…";
        try {
            const result = await jsonrpc("/contact/submit", {
                first_name: this._val("ct-first"),
                last_name: this._val("ct-last"),
                email: this._val("ct-email"),
                phone: this._val("ct-phone"),
                department: this._val("ct-dept"),
                message: this._val("ct-msg"),
            });
            if (result.success) {
                this.form.style.display = "none";
                this.el.querySelector("#ct-success").style.display = "flex";
            } else {
                this._setError(result.error || "Something went wrong. Please try again.");
            }
        } catch {
            this._setError("Network error. Please check your connection and try again.");
        } finally {
            this.btn.disabled = false;
            this.btn.innerHTML = this.btnHtml;
        }
    },

    _onReset() {
        this.form.reset();
        this.form.style.display = "block";
        this._setError("");
        this.el.querySelector("#ct-success").style.display = "none";
    },

    _onFaqClick(ev) {
        const item = ev.currentTarget.closest(".ct-faq-item");
        const wasOpen = item.classList.contains("open");
        this.el.querySelectorAll(".ct-faq-item").forEach((i) => i.classList.remove("open"));
        if (!wasOpen) {
            item.classList.add("open");
        }
    },
});
