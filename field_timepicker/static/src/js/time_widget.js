/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import time from 'web.time';
const { Component, useRef } = owl;
var Dialog = require('web.Dialog');

/**
 * We define this module for the function of creating a time picker widget
 *
 */

export class FieldTimePicker extends Component {
    static template = 'FieldTimePicker';

    setup() {
        super.setup();
        this.input = useRef('input_time');
        useInputField({ getValue: () => this.props.value || "", refName: "input_time" });
    }

    /**
     * Click function to validate weather its a char field if yes it will show
       the timepicker else show a waring
     *
     */

    _onClickTimeField(event) {
        var self = this;
        var $input = $(event.currentTarget);
        if (this.input.el && this.props.type === "char"){
          this.props.update(this.input.el.value.replace(FieldTimePicker, ''));
           $input.wickedpicker({
            twentyFour: true,
            title: 'Select Time',
            showSeconds: true,
        });
        $input.wickedpicker('open');
       }
       else{
        Dialog.alert(this,
        "Only Supported for 'char' type please change field type to 'char'")
        return false;
       }
    }
}

registry.category("fields").add("timepicker", FieldTimePicker);
