/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { Component,useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
export class DatePickerField extends Component {
    /**
     * Define the template for the DatePickerField component.
     * The template name should match the one used in the XML template.
     */
    static template = 'FieldDateMultipleDate'
    setup() {
        this.input = useRef("inputdate");
        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            refName: "inputdate"
        });
    }
    /**
     * Handle the event when the date field is selected.
     * Initializes and displays the date picker.
     *
     * @param {Event} ev - The event object.
     */
    _onSelectDateField(ev) {
        var dateFormat = "MM/DD/YYYY";
        dateFormat = dateFormat.toLowerCase()
        if (this.input.el) {
            if (this.input.el.value) {
                this.props.record.update({
                    [this.props.name]: this.input.el.value
                })
            }
            $(this.input.el).datepicker({
                multidate: true,
                format: dateFormat,
            }).trigger('focus');
        }
    }
}
/**
 * Configuration for the datepickerField.
 */
DatePickerField.props = {
    ...standardFieldProps,
}
export const datepickerField = {
    component: DatePickerField,
    supportedTypes: ["char"],
};
registry.category("fields").add("multiple_datepicker", datepickerField);
