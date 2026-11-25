/**
 * Petzen services page: "Request an Appointment" form, sent to /petzen/booking
 * (creates a CRM lead). The "Book" buttons of the service cards, and the
 * ?service= parameter of the links of the home page, preselect the service.
 */
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

export class PetzenBookingForm extends Interaction {
    static selector = ".pz-page-services";
    dynamicContent = {
        "[data-pz-service]": { "t-on-click": this.onBookClick },
        "#booking-form": { "t-on-submit.prevent.withTarget": this.locked(this.onSubmit) },
    };

    start() {
        this.form = this.el.querySelector("#booking-form");
        const dateInput = this.form?.querySelector("#booking-date");
        if (dateInput) {
            // today, in the visitor's time zone (YYYY-MM-DD)
            const now = new Date();
            dateInput.min = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
                .toISOString()
                .slice(0, 10);
        }
        const service = new URLSearchParams(window.location.search).get("service");
        if (service) {
            this.selectService(service);
        }
    }

    /**
     * @param {string} service value of an option of the "Service" select
     */
    selectService(service) {
        const select = this.form?.querySelector("#booking-service");
        if (select && [...select.options].some((option) => option.value === service)) {
            select.value = service;
        }
    }

    /**
     * @param {MouseEvent} ev
     */
    onBookClick(ev) {
        this.selectService(ev.currentTarget.dataset.pzService);
    }

    /**
     * @param {string} msg error message, empty to hide the banner
     */
    setError(msg) {
        const banner = this.form.querySelector("#booking-error-banner");
        banner.querySelector("#booking-error-text").textContent = msg || "";
        banner.classList.toggle("visible", !!msg);
    }

    /**
     * @param {SubmitEvent} ev
     * @param {HTMLFormElement} form
     */
    async onSubmit(ev, form) {
        const btn = form.querySelector("button[type=submit]");
        const btnText = btn.textContent;
        const success = form.querySelector("#booking-success");
        btn.disabled = true;
        btn.textContent = _t("Sending…");
        this.setError("");
        success.classList.remove("visible");
        const value = (name) => (form.elements[name]?.value || "").trim();
        try {
            const result = await this.waitFor(rpc("/petzen/booking", {
                name: value("name"),
                email: value("email"),
                phone: value("phone"),
                date: value("date"),
                service: value("service"),
                notes: value("notes"),
                website_url: value("website_url"),
            }));
            if (result.success) {
                form.reset();
                success.classList.add("visible");
            } else {
                this.setError(result.error || _t("Something went wrong. Please try again."));
            }
        } catch {
            this.setError(_t("Network error. Please check your connection and try again."));
        } finally {
            btn.disabled = false;
            btn.textContent = btnText;
        }
    }
}

registry.category("public.interactions").add("theme_petzen.booking_form", PetzenBookingForm);
