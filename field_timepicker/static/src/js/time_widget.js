/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
const { Component, useRef } = owl;
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
/**
 * We define this module for the function of creating a time picker widget
 */
export class FieldTimePicker extends Component {
    static template = 'FieldTimePicker';
    setup() {
        this.input = useRef('input_time');
        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            refName: "input_time"
        });
    }
    /**
     * Click function to validate weather its a char field if yes it will show
       the timepicker else show a waring
     */
    _onClickTimeField(ev) {
        var self = this;
        if (this.props.record.fields[this.props.name].type == "char") {
        var $input = $(ev.currentTarget);
        this.props.record.update({[this.props.name]: this.input.el.value})
        $input.wickedpicker({
            twentyFour: true,
            title: 'Select Time',
            showSeconds: true,
        });
        $input.wickedpicker('open');
        }else{
            this.env.model.dialog.add(AlertDialog, {
            body: _t("This widget can only be added to 'Char' field"),
        });
        }
    }
}
FieldTimePicker.props = {
    ...standardFieldProps,
}
export const TimePickerField = {
    component: FieldTimePicker,
    supportedTypes: ["char"],
};
registry.category("fields").add("timepicker", TimePickerField);
