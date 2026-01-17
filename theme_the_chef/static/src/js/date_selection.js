/** @odoo-module **/
// Date Selection
import publicWidget from "@web/legacy/js/public/public_widget";

const DateSelection = publicWidget.Widget.extend({
    selector: '.booking',

    start() {
        this._onClick();
    },

    _onClick() {
        const datePicker = this.$el.find('#date-picker');
        if (datePicker.length) {
            datePicker[0].min = new Date().toISOString().split("T")[0];
        }
    },
});

publicWidget.registry.booking = DateSelection;
export default DateSelection;

