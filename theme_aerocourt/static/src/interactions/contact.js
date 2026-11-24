/** Interactions of the contact page: request form and FAQ items. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";
import { clearFieldError, fieldError, formError, setLoading, validateForm } from "./forms";
import { register } from "./services";

/** Contact form: counter, validation, and the enquiry saved as a CRM lead. */
export class AcContactForm extends Interaction {
    static selector = "#contactPage, .s_aerocourt_contact";
    dynamicContent = {
        "#contactForm": {
            "t-on-input": clearFieldError,
            "t-on-submit": this.onSubmit,
        },
        "#c-message-count": {
            "t-out": () => `${this.message.value.length} / ${this.message.maxLength}`,
            "t-att-class": () => ({ "is-near": this.message.value.length > this.message.maxLength * 0.9 }),
        },
        "#contactAgain": { "t-on-click": this.onAgain },
    };

    setup() {
        this.form = this.el.querySelector("#contactForm");
        this.message = this.el.querySelector("#c-message");
    }

    async onSubmit(ev) {
        ev.preventDefault();
        const form = this.form;
        if (!validateForm(form)) {
            return;
        }
        if (this.message.value.trim().length < 10) {
            fieldError(form, "message", _t("Please add a little more detail (at least 10 characters)."));
            return;
        }
        const data = Object.fromEntries(new FormData(form));
        const button = form.querySelector('button[type="submit"]');
        setLoading(button, true, _t("Sending…"));
        try {
            const res = await this.waitFor(register("contact", data));
            this.showSuccess(data, res.reference);
        } catch (error) {
            formError(form, error.message);
        } finally {
            setLoading(button, false);
        }
    }

    showSuccess(data, reference) {
        const success = document.getElementById("contactSuccess");
        document.getElementById("contactSuccessText").textContent = _t(
            "Thanks, %(name)s! We've got your %(topic)s enquiry and will reply to %(email)s within one working day.",
            {
                name: data.name.trim().split(" ")[0],
                topic: data.topic.toLowerCase(),
                email: data.email,
            }
        );
        document.getElementById("contactRef").textContent = `${_t("Reference")} · ${reference}`;
        document.getElementById("contactFormWrap").hidden = true;
        success.hidden = false;
        success.focus();
    }

    onAgain() {
        this.form.reset();
        document.getElementById("contactSuccess").hidden = true;
        document.getElementById("contactFormWrap").hidden = false;
        this.form.querySelector("#c-name").focus();
    }
}

/** Keeps one FAQ answer open at a time. */
export class AcFaqItem extends Interaction {
    static selector = ".ac-faq-item";
    dynamicContent = {
        _root: { "t-on-toggle": this.onToggle },
    };

    onToggle() {
        if (this.el.open) {
            this.el.parentElement
                .querySelectorAll(".ac-faq-item")
                .forEach((other) => other !== this.el && (other.open = false));
        }
    }
}

const category = registry.category("public.interactions");
category.add("theme_aerocourt.contact_form", AcContactForm);
category.add("theme_aerocourt.faq_item", AcFaqItem);
