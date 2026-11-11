import { Component, signal } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";

/**
 * We define this module for the function of creating a time picker widget
 */
export class FieldTimePicker extends Component {
    static template = "FieldTimePicker";
    static supportedTypes = ["char"];
    inputRef = signal.ref();

    setup() {
        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            ref: this.inputRef,
        });
    }
}

export const timepicker = {
    component: FieldTimePicker,
};

// Add the timepicker to the fields category
registry.category("fields").add("timepicker_time", timepicker);
