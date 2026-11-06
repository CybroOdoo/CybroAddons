import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const MINIMUM_AGE = 18;
const STORAGE_KEY = "age_verification_odoo.verified";

/**
 * @param {Date} birthDate date of birth
 * @param {Date} today current date
 * @returns {boolean} true when the person reached the minimum age
 */
export function isOldEnough(birthDate, today = new Date()) {
    const adultDate = new Date(birthDate);
    adultDate.setFullYear(birthDate.getFullYear() + MINIMUM_AGE);
    return adultDate <= today;
}

/**
 * Keep the signup form locked until the visitor confirms a date of birth of
 * at least the minimum age. Invitation links already carry the login of a
 * known user, so they skip the popup.
 */
export class AgeVerification extends Interaction {
    static selector = ".oe_website_login_container:has(.o_age_verify)";
    dynamicContent = {
        ".o_age_verify_submit": { "t-on-click": this.onSubmit },
    };

    setup() {
        this.popup = this.el.querySelector(".o_age_verify");
        this.form = this.el.querySelector(".oe_signup_form");
        this.fields = this.form.querySelectorAll("input, select, textarea, button");
        const login = this.form.querySelector('input[name="login"]');
        if (login?.value || browser.sessionStorage.getItem(STORAGE_KEY)) {
            this.unlockForm();
        } else {
            // website.auth_form drives the disabled state of the submit button
            this.form.inert = true;
            this.fields.forEach((field) => (field.disabled = true));
        }
    }

    unlockForm() {
        this.popup.classList.add("d-none");
        this.form.inert = false;
        this.fields.forEach((field) => (field.disabled = false));
    }

    showMessage(selector) {
        for (const message of this.popup.querySelectorAll(
            ".o_age_verify_invalid, .o_age_verify_denied"
        )) {
            message.classList.toggle("d-none", !message.matches(selector));
        }
    }

    onSubmit() {
        const birthDate = this.popup.querySelector(".o_age_verify_date").valueAsDate;
        if (!birthDate || birthDate > new Date()) {
            this.showMessage(".o_age_verify_invalid");
        } else if (isOldEnough(birthDate)) {
            browser.sessionStorage.setItem(STORAGE_KEY, "1");
            this.unlockForm();
        } else {
            this.showMessage(".o_age_verify_denied");
        }
    }
}

registry.category("public.interactions").add("age_verification_odoo.age_verification", AgeVerification);
