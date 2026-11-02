import { Component, signal, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Time picker (<input type="time">) for a char field holding the time as HH:MM.
 */
export class FieldTimePicker extends Component {
    static template = "FieldTimePicker";
    props = useProps(standardFieldProps);
    input = signal.ref();

    setup() {
        useInputField({
            ref: this.input,
            getValue: () => this.props.record.data[this.props.name] || "",
        });
    }

    onBlur() {
        /* Commit the picked time to the record. */
        this.props.record.update({ [this.props.name]: this.input()?.value });
    }
}

export const timepicker = {
    component: FieldTimePicker,
    supportedTypes: ["char"],
};

// Add the timepicker to the fields category
registry.category("fields").add("timepicker_time", timepicker);
