/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EducationalContactPhone = publicWidget.Widget.extend({
    selector: '.section-contact-form',
    events: {
        'input input[name="phone"]': '_onPhoneInput',
    },

    /**
     * Strip letters and other invalid characters from the phone number field,
     * keeping only digits, spaces, '+', '-' and parentheses.
     *
     * @param {Event} ev
     */
    _onPhoneInput(ev) {
        const input = ev.currentTarget;
        const cleaned = input.value.replace(/[^0-9+\-() ]/g, '');
        if (cleaned !== input.value) {
            input.value = cleaned;
        }
    },
});
