/**
 * Propelle form and page interactions.
 *
 * The valuation form that continues into the booking page, the listing alert
 * form, the status filter and the showcase of the Projects page, and the
 * prefill of the contact and registration forms from the links of the site.
 * The contact and registration forms themselves are the standard website
 * forms.
 */
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { scrollToElement, prefersReducedMotion } from "@theme_propelle/js/propelle_core";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const PHONE_RE = /^[+()\d\s.-]{7,20}$/;

/**
 * Valuation form of the Sell page: checks the fields and continues into the
 * booking page, with the property and the contact details carried over.
 */
export class PropelleValuationForm extends Interaction {
    static selector = "#valuation-form";
    dynamicContent = {
        _root: { "t-on-submit.prevent": this.onSubmit },
        "input": { "t-on-input": this.onInput },
    };

    field(id) {
        return this.el.querySelector("#" + id);
    }

    setError(input, message) {
        const field = input.closest(".pp-field");
        field.classList.toggle("pp-has-error", Boolean(message));
        input.setAttribute("aria-invalid", message ? "true" : "false");
        field.querySelector(".pp-field__error").textContent = message || "";
    }

    onInput(ev) {
        if (ev.currentTarget.getAttribute("aria-invalid") === "true") {
            this.setError(ev.currentTarget, "");
        }
    }

    onSubmit() {
        const status = this.el.querySelector("#valuation-status");
        const address = this.field("v-address");
        const name = this.field("v-name");
        const email = this.field("v-email");
        const phone = this.field("v-phone");
        const checks = [
            [address, address.value.trim().length >= 5 ? "" : "Please enter the property address."],
            [name, name.value.trim().length >= 2 ? "" : "Please enter your name."],
            [email, EMAIL_RE.test(email.value.trim()) ? "" : "Please enter a valid email address."],
            [
                phone,
                !phone.value.trim() || PHONE_RE.test(phone.value.trim())
                    ? ""
                    : "That phone number doesn't look right.",
            ],
        ];
        for (const [input, message] of checks) {
            this.setError(input, message);
        }
        const invalid = checks.find(([, message]) => message);
        if (invalid) {
            invalid[0].focus();
            status.className = "pp-form-status pp-is-error";
            status.textContent = "Please check the fields above.";
            return;
        }
        const type = this.field("v-type").value;
        const query = new URLSearchParams({
            type: "sell",
            step: "2",
            address: address.value.trim(),
            city: this.field("v-city").value,
            ptype: type.charAt(0).toUpperCase() + type.slice(1),
            beds: this.field("v-beds").value,
            name: name.value.trim(),
            email: email.value.trim(),
            phone: phone.value.trim(),
        });
        status.className = "pp-form-status pp-is-success";
        status.textContent = "Great, now pick a time for the visit…";
        window.location.href = "/booking?" + query;
    }
}

/**
 * Request for new listing alerts: saved as a lead of the sales team.
 */
export class PropelleAlertForm extends Interaction {
    static selector = "#alert-form";
    dynamicContent = {
        _root: { "t-on-submit.prevent": this.onSubmit },
    };

    setStatus(kind, message) {
        const status = this.el.closest("section").querySelector("#alert-status");
        status.className = `pp-form-status pp-form-status--light pp-is-${kind}`;
        status.textContent = message;
    }

    async onSubmit() {
        const input = this.el.querySelector("#a-email");
        const value = input.value.trim();
        if (!EMAIL_RE.test(value)) {
            this.el.classList.add("pp-has-error");
            input.setAttribute("aria-invalid", "true");
            this.setStatus(
                "error",
                value ? "That email address doesn't look right." : "Please enter your email address."
            );
            input.focus();
            return;
        }
        this.el.classList.remove("pp-has-error");
        input.setAttribute("aria-invalid", "false");
        const select = this.el.querySelector("#a-city");
        const result = await this.waitFor(
            rpc("/propelle/alert", { email: value, city: select.value }).catch(() => null)
        );
        if (!result || result.error) {
            this.setStatus("error", (result && result.error) || "Something went wrong, please try again.");
            return;
        }
        this.setStatus("success", `Done. We'll email ${value} when new homes come up in ${result.city}.`);
        this.el.reset();
    }
}

/**
 * Status filter of the Projects page.
 */
export class PropelleProjectFilters extends Interaction {
    static selector = "[data-project-filters]";
    dynamicContent = {
        ".pp-filter-btn": { "t-on-click": this.onClick },
    };

    onClick(ev) {
        const status = ev.currentTarget.dataset.projectFilter;
        const section = this.el.closest("section");
        const cards = section.querySelectorAll("[data-project-status]");
        let visible = 0;
        for (const card of cards) {
            const show = status === "all" || card.dataset.projectStatus === status;
            card.classList.toggle("pp-is-hidden", !show);
            if (show) {
                visible++;
            }
        }
        for (const btn of this.el.querySelectorAll(".pp-filter-btn")) {
            const on = btn.dataset.projectFilter === status;
            btn.classList.toggle("pp-is-active", on);
            btn.setAttribute("aria-pressed", String(on));
        }
        const count = section.querySelector(".pp-project-count");
        if (count) {
            count.textContent = visible === 1 ? "1 project" : `${visible} projects`;
        }
    }
}

/**
 * Featured project of the Projects page: the thumbnails switch the photo and
 * the card.
 */
export class PropelleShowcase extends Interaction {
    static selector = "[data-showcase]";
    dynamicContent = {
        "[data-show]": { "t-on-click": this.onClick },
    };

    field(key) {
        return this.el.querySelector(`[data-show-${key}]`);
    }

    onClick(ev) {
        const thumb = ev.currentTarget;
        const index = thumb.dataset.show;
        for (const img of this.el.querySelectorAll("[data-show-img]")) {
            img.classList.toggle("pp-is-hidden-img", img.dataset.showImg !== index);
        }
        for (const btn of this.el.querySelectorAll("[data-show]")) {
            const on = btn === thumb;
            btn.classList.toggle("pp-is-active", on);
            btn.setAttribute("aria-pressed", String(on));
        }
        this.field("name").textContent = thumb.dataset.name;
        this.field("loc").textContent = thumb.dataset.loc;
        this.field("from").textContent = thumb.dataset.from;
        this.field("units").textContent = thumb.dataset.units;
        this.field("done").textContent = thumb.dataset.done;
        const status = this.field("status");
        status.textContent = thumb.dataset.status;
        status.className = `pp-availability pp-availability--${thumb.dataset.statusClass}`;
    }
}

/**
 * Registration form of the Projects page: "Register interest" buttons and
 * `?project=` links choose the project of the standard form.
 */
export class PropelleRegister extends Interaction {
    static selector = ".pp-register-project";

    start() {
        const fromUrl = new URLSearchParams(window.location.search).get("project");
        if (fromUrl) {
            this.select(fromUrl);
        }
        this.addListener(document.body, "click", this.onRegisterClick);
    }

    select(name) {
        const option = Array.from(this.el.options).find((opt) => opt.dataset.project === name);
        if (option) {
            this.el.value = option.value;
            this.el.dispatchEvent(new Event("change", { bubbles: true }));
        }
    }

    onRegisterClick(ev) {
        const button = ev.target.closest("[data-register]");
        if (!button) {
            return;
        }
        this.select(button.dataset.register);
        const target = this.el.closest("section");
        if (target) {
            scrollToElement(target);
            const name = target.querySelector("#pp_register_name");
            setTimeout(() => name && name.focus({ preventScroll: true }), prefersReducedMotion() ? 0 : 500);
        }
    }
}

/**
 * Contact form: `/contactus?viewing=Home` fills the interest and the message.
 */
export class PropelleContactPrefill extends Interaction {
    static selector = "#pp_contact_interest";

    start() {
        const viewing = new URLSearchParams(window.location.search).get("viewing");
        if (!viewing) {
            return;
        }
        this.el.selectedIndex = 0;
        this.el.dispatchEvent(new Event("change", { bubbles: true }));
        const message = this.el.closest("form").querySelector("#pp_contact_message");
        if (message && !message.value) {
            message.value = `Hi, I'd like to arrange a viewing of ${viewing.slice(0, 120)}.`;
        }
    }
}

registry
    .category("public.interactions")
    .add("theme_propelle.valuation_form", PropelleValuationForm)
    .add("theme_propelle.alert_form", PropelleAlertForm)
    .add("theme_propelle.project_filters", PropelleProjectFilters)
    .add("theme_propelle.showcase", PropelleShowcase)
    .add("theme_propelle.register", PropelleRegister)
    .add("theme_propelle.contact_prefill", PropelleContactPrefill);
