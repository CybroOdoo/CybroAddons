/** @odoo-module **/

import { Subscribe } from "@website_mass_mailing/interactions/subscribe";
import { patch } from "@web/core/utils/patch";

patch(Subscribe.prototype, {
    _updateView(data) {
        super._updateView(...arguments);
        const valueInputEl = this.el.querySelector('input.js_subscribe_value, input.js_subscribe_email');
        if (valueInputEl) {
            valueInputEl.value = '';
        }
    }
});
