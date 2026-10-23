import { Component, proxy, signal, t, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePopover } from "@web/core/popover/popover_hook";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class TimePickerPopover extends Component {
    static template = "field_timepicker.TimePickerPopover";
    props = useProps({
        close: t.function().optional(),
        currentTime: t.string().optional(),
        onTimeSelected: t.function().optional(),
    });

    setup() {
        const [hour = 0, minute = 0, second = 0] = (this.props.currentTime || "00:00:00")
            .split(":")
            .map(Number);
        this.state = proxy({
            hour: isNaN(hour) ? 0 : hour,
            minute: isNaN(minute) ? 0 : minute,
            second: isNaN(second) ? 0 : second,
        });
    }

    get hourLabel() {
        return _t("Hour");
    }

    get minuteLabel() {
        return _t("Minute");
    }

    get secondLabel() {
        return _t("Second");
    }

    get cancelLabel() {
        return _t("Cancel");
    }

    get confirmLabel() {
        return _t("Set Time");
    }

    formatValue(val) {
        return val < 10 ? `0${val}` : `${val}`;
    }

    increment(unit, max) {
        this.state[unit] = (this.state[unit] + 1) % (max + 1);
    }

    decrement(unit, max) {
        this.state[unit] = (this.state[unit] - 1 + (max + 1)) % (max + 1);
    }

    onConfirm() {
        const selectedTime = `${this.formatValue(this.state.hour)}:${this.formatValue(
            this.state.minute
        )}:${this.formatValue(this.state.second)}`;
        if (this.props.onTimeSelected) {
            this.props.onTimeSelected(selectedTime);
        }
        if (this.props.close) {
            this.props.close();
        }
    }

    onCancel() {
        if (this.props.close) {
            this.props.close();
        }
    }
}

export class FieldTimePicker extends Component {
    static template = "field_timepicker.FieldTimePicker";
    props = useProps(standardFieldProps);

    input = signal.ref();

    setup() {
        useInputField({
            ref: this.input,
            getValue: () => this.props.record.data[this.props.name] || "",
        });
        this.dialog = useService("dialog");
        this.popover = usePopover(TimePickerPopover, {
            position: "bottom-start",
        });
    }

    _onClickTimeField(ev) {
        if (this.props.readonly) {
            return;
        }
        const inputEl = this.input.el || (typeof this.input === "function" ? this.input() : null);
        if (!inputEl) {
            return;
        }
        if (this.props.record.fields[this.props.name].type !== "char") {
            this.dialog.add(AlertDialog, {
                body: _t("This widget can only be added to a 'Char' field."),
            });
            return;
        }
        if (this.popover.isOpen) {
            this.popover.close();
            return;
        }
        const currentTime = inputEl.value || "00:00:00";
        this.popover.open(inputEl, {
            currentTime,
            onTimeSelected: (selectedTime) => {
                this.props.record.update({ [this.props.name]: selectedTime });
            },
        });
    }
}

export const TimePickerField = {
    component: FieldTimePicker,
    supportedTypes: ["char"],
};

registry.category("fields").add("timepicker", TimePickerField);
