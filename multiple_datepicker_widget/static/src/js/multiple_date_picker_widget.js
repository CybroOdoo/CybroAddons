import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { Component, signal, onMounted, onWillUnmount, useEffect } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Formats a Date object or date string into 'YYYY-MM-DD' using local date components.
 * This ensures that dates selected in timezones east of UTC are not shifted by one day
 * (which occurs when using date.toISOString() because of UTC conversion).
 *
 * @param {Date|string} date
 * @returns {string}
 */
export function formatLocalDate(date) {
    if (!date) {
        return "";
    }
    if (typeof date === "string") {
        return date.trim();
    }
    if (date instanceof Date && !isNaN(date.getTime())) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
    }
    return String(date);
}

export class DatePickerField extends Component {
    static template = "multiple_datepicker_widget.DatePickerField";

    setup() {
        this.input = signal.ref("input");

        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            ref: this.input,
        });

        onMounted(() => {
            if (!this.props.readonly) {
                this.initializeFlatpickr();
            }
        });

        useEffect(
            () => {
                if (!this.props.readonly && !this.fpInstance && this.input()) {
                    this.initializeFlatpickr();
                } else if (this.props.readonly && this.fpInstance) {
                    this.fpInstance.destroy();
                    this.fpInstance = null;
                }
            },
            () => [this.props.readonly]
        );

        useEffect(
            () => {
                if (this.fpInstance) {
                    const rawValue = this.props.record.data[this.props.name];
                    const dates = rawValue
                        ? rawValue.split(",").map((d) => d.trim()).filter(Boolean)
                        : [];
                    const currentSelected = this.fpInstance.selectedDates.map(formatLocalDate);
                    if (dates.join(",") !== currentSelected.join(",")) {
                        this.fpInstance.setDate(dates, false);
                    }
                }
            },
            () => [this.props.record.data[this.props.name]]
        );

        onWillUnmount(() => {
            if (this.fpInstance) {
                this.fpInstance.destroy();
                this.fpInstance = null;
            }
        });
    }

    initializeFlatpickr() {
        const input = this.input();
        const flatpickrFn = window.flatpickr;

        if (input && !this.fpInstance && flatpickrFn) {
            const rawValue = this.props.record.data[this.props.name];
            const defaultDates = rawValue
                ? rawValue.split(",").map((d) => d.trim()).filter(Boolean)
                : [];

            this.fpInstance = flatpickrFn(input, {
                mode: "multiple",
                dateFormat: "Y-m-d",
                clickOpens: !this.props.readonly,
                defaultDate: defaultDates,
                onChange: (selectedDates) => {
                    const newValue = selectedDates
                        .map(formatLocalDate)
                        .filter(Boolean)
                        .join(",");

                    if (this.props.record.data[this.props.name] !== newValue) {
                        this.props.record.update({
                            [this.props.name]: newValue,
                        });
                    }
                },
            });
        }
    }

    _onSelectDateField() {
        if (this.props.readonly) {
            return;
        }

        const input = this.input();
        if (!input) {
            return;
        }

        if (!this.fpInstance) {
            this.initializeFlatpickr();
        }

        input.focus();
        if (this.fpInstance) {
            this.fpInstance.open();
        }
    }
}

DatePickerField.props = {
    ...standardFieldProps,
};

export const datepickerField = {
    component: DatePickerField,
    supportedTypes: ["char"],
};

registry.category("fields").add(
    "multiple_datepicker",
    datepickerField
);
