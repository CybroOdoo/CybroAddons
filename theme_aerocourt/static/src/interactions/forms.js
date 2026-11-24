/** Form helpers: field markup, validation and error display. */

import { _t } from "@web/core/l10n/translation";
import { escapeHTML } from "./utils";

/* Markup and validation of the forms shown in the modal and on the contact page. */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/** Renders a labelled input with an associated error message. */
export const fieldHTML = ({
    name,
    label,
    type = "text",
    required = true,
    autocomplete = "off",
    placeholder = "",
    full = false,
}) => `
    <div class="ac-field${full ? " ac-modal-form__full" : ""}">
      <label class="ac-field__label" for="f-${name}">${label}${required ? "" : ` <small>(${_t("optional")})</small>`}</label>
      <input class="ac-input" id="f-${name}" name="${name}" type="${type}" ${required ? "required" : ""}
             autocomplete="${autocomplete}" placeholder="${placeholder}" aria-describedby="f-${name}-error" />
      <p class="ac-field__error" id="f-${name}-error" data-error-for="${name}"></p>
    </div>`;

export const selectHTML = ({ name, label, options, full = false }) => `
    <div class="ac-field${full ? " ac-modal-form__full" : ""}">
      <label class="ac-field__label" for="f-${name}">${label}</label>
      <select class="ac-input" id="f-${name}" name="${name}" required aria-describedby="f-${name}-error">
        <option value="">${_t("Select…")}</option>
        ${options.map((o) => `<option>${escapeHTML(o)}</option>`).join("")}
      </select>
      <p class="ac-field__error" id="f-${name}-error" data-error-for="${name}"></p>
    </div>`;

/** Validates required fields, emails, radios and checkboxes. Returns true when valid. */
export function validateForm(form) {
    const names = new Set();
    for (const el of form.elements) {
        if (el.name && el.required) {
            names.add(el.name);
        }
    }

    let firstInvalid = null;
    names.forEach((name) => {
        const ctrl = form.elements[name];
        const first = ctrl instanceof RadioNodeList ? ctrl[0] : ctrl;
        let message = "";

        if (first.type === "radio") {
            if (!(ctrl instanceof RadioNodeList ? ctrl.value : ctrl.checked)) {
                message = _t("Please choose an option.");
            }
        } else if (first.type === "checkbox") {
            if (!first.checked) {
                message = _t("Please confirm to continue.");
            }
        } else {
            const value = first.value.trim();
            if (!value) {
                message = _t("This field is required.");
            } else if (first.type === "email" && !EMAIL_RE.test(value)) {
                message = _t("Please enter a valid email address.");
            }
        }

        const errorEl = form.querySelector(`[data-error-for="${name}"]`);
        if (errorEl) {
            errorEl.textContent = message;
        }
        const group = ctrl instanceof RadioNodeList ? Array.from(ctrl) : [first];
        group.forEach((el) => el.setAttribute("aria-invalid", message ? "true" : "false"));
        if (message && !firstInvalid) {
            firstInvalid = first;
        }
    });

    firstInvalid?.focus();
    return !firstInvalid;
}

/** Shows an error under one field and puts the focus on it. */
export function fieldError(form, name, message) {
    const control = form.elements[name];
    form.querySelector(`[data-error-for="${name}"]`).textContent = message;
    control.setAttribute("aria-invalid", "true");
    control.focus();
}

/** Shows a message under a form, for errors that belong to no field. */
export function formError(form, message) {
    let el = form.querySelector("[data-form-error]");
    if (!el) {
        el = document.createElement("p");
        el.className = "ac-field__error";
        el.dataset.formError = "";
        el.setAttribute("role", "alert");
        form.insertBefore(
            el,
            form.querySelector(".ac-modal-actions") || form.lastElementChild
        );
    }
    el.textContent = message;
}

/** Clears the error of a field as soon as the visitor corrects it. */
export function clearFieldError(ev) {
    const input = ev.target;
    const form = input.closest("form");
    if (!input.name || !form) {
        return;
    }
    const errorEl = form.querySelector(`[data-error-for="${input.name}"]`);
    if (errorEl?.textContent) {
        errorEl.textContent = "";
        input.setAttribute("aria-invalid", "false");
    }
}

/** Puts a button in its loading state, and back. */
export function setLoading(btn, loading, label = _t("Processing…")) {
    if (!btn) {
        return;
    }
    btn.classList.toggle("is-loading", loading);
    btn.disabled = loading;
    const labelEl = btn.querySelector(".ac-btn__label") || btn;
    if (loading) {
        btn.dataset.label = labelEl.textContent;
        labelEl.textContent = label;
    } else if (btn.dataset.label) {
        labelEl.textContent = btn.dataset.label;
    }
}
