/** @odoo-module **/

/**
 * This module provides client-side validation for contact forms
 * within the Tennis Court theme. It ensures that all required
 * fields are filled out before the form is submitted.
 */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.TcContactForm = publicWidget.Widget.extend({
    selector: "form#contactus_form, .join-form-wrapper form",
    events: {
        "click .s_website_form_send": "_onSendClick",
    },
    /**
     * Handles the click event on the form's send button.
     * Validates all required fields and prevents submission if any are empty.
     *
     * @private
     * @param {Event} ev
     */
    _onSendClick(ev) {
        const form = this.el;
        form.classList.add("was-validated");
        let hasError = false;
        // Select all required fields in the form
        const requiredFields = form.querySelectorAll("[required]");
        requiredFields.forEach(function (field) {
            if (!field.value.trim()) {
                field.classList.add("tc-field-error");
                hasError = true;
            } else {
                field.classList.remove("tc-field-error");
            }
        });
        if (hasError) {
            ev.preventDefault();
            ev.stopPropagation();
        }
    },
});
