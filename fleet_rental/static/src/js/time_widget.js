/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
const { Component, useRef } = owl;
/**
 * We define this module for the function of creating a time picker widget
 *
 */
class FieldTimePicker extends Component {
    setup() {
        this.input = useRef('input_time');
        useInputField({ getValue: () => this.props.record.data[this.props.name] || "", refName: "input_time" });
    }

    onBlur(){
        /**
         * Handle the blur event for the timepicker input field.
         *
         * This function is responsible for handling the blur event on the timepicker input field.
         * It checks if the close button is present in the timepicker, and if so, it adds a click event
         * listener to it to handle the closing of the timepicker.
         *
         * @returns {void}
         */
         this.props.record.update({ [this.props.name] : this.input.el?.value})
    }
}
// Set the template for the FieldTimePicker component
FieldTimePicker.template = 'FieldTimePicker';
FieldTimePicker.supportedTypes = ["char"]
// Add the timepicker to the fields category
registry.category("fields").add("timepicker_time", FieldTimePicker);
