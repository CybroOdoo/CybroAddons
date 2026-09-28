/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

$(function () {
    if (localStorage.getItem('current_vehicle')) {
        localStorage.removeItem('current_vehicle');
    }
});

publicWidget.registry.Request = publicWidget.Widget.extend({
    selector: '.submit_boolean_on',
    start: function () {
        this._super.apply(this, arguments);
        if (localStorage.getItem('current_vehicle')) {
            localStorage.removeItem('current_vehicle');
        }
    }
});
