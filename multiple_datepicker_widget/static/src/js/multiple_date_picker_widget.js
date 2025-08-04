/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { Component, useRef, onMounted } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class DatePickerField extends Component {
    static template = 'FieldDateMultipleDate';

    setup() {
        // Reference for the input element
        this.input = useRef("inputdate");

        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            refName: "inputdate",
        });

        onMounted(() => {
            this.initializeFlatpickr();
        });
    }

    // Initialize the Flatpickr datepicker with multiple date selection
    initializeFlatpickr() {
        if (this.input.el && !this.fpInstance) {
            this.fpInstance = flatpickr(this.input.el, {
                mode: "multiple",
                dateFormat: "Y-m-d",
                defaultDate: this.props.record.data[this.props.name]
                    ? this.props.record.data[this.props.name].split(",")
                    : [],
                onChange: (selectedDates) => {
                    const newValue = selectedDates.map(d => d.toISOString().split("T")[0]).join(",");
                    if (this.props.record.data[this.props.name] !== newValue) {
                        this.props.record.update({
                            [this.props.name]: newValue,
                        });
                    }
                },
            });
        }
    }


    // Handle the click event to trigger Flatpickr on the input field
    _onSelectDateField(ev) {
        if (!this.input.el._flatpickr) {
            this.initializeFlatpickr();
        }
        this.input.el.focus();
    }
}

// Define the component's props
DatePickerField.props = {
    ...standardFieldProps,
};

// Register the custom field in the Odoo registry
export const datepickerField = {
    component: DatePickerField,
    supportedTypes: ["char"],
};

registry.category("fields").add("multiple_datepicker", datepickerField);
