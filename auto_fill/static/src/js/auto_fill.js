/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { _t } from "@web/core/l10n/translation";
import { Component,useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Dialog } from "@web/core/dialog/dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { jsonrpc } from "@web/core/network/rpc_service";
export class FieldAutoFill extends Component {
    /**
     * Define the template for the DatePickerField component.
     * The template name should match the one used in the XML template.
     */
    static template = 'FieldAutoFill'
    setup() {
        super.setup();
        this.input = useRef('input_data');
        useInputField({
            getValue: () => this.props.value || "",
            refName: "input_data"
        });
        var values = this.props.record._values
        for (const key in values) {
          if (values.hasOwnProperty(key)) {
            const value = values[key];
            if (key == this.props.name){
                this.props.value = values[key]
            }
          }
        }
        $('.o_form_button_save').click(() => {
            this.props.value = $('#input_field_auto_fill').val()
            })
    }
    /**
     *Its a keyup function which will display the values according to key pressed
     */
    _onKeyup(ev) {
        var value = ev.target.value;
        var model = this.env.model.env.searchModel.resModel
        var self=this;
        var values = this.__owl__.props.record._config.fields
        for (const key in values) {
          if (values.hasOwnProperty(key)) {
            if (values[key].name == this.props.name){
                this.props.type = values[key].type
            }
          }
        }
        if(this.props.type === "char") {
            this.env.model.rpc('/matching/records',{
                    model: model,
                    field: this.props.name,
                    value: value,
                })
                .then(function(result) {
                    if(result.length > 0) {
                        self.input.el.nextSibling.style.display = 'block';
                        var table = self.input.el.nextSibling;
                        $(table).find('tr').remove();
                        var i;
                        for(i = 0; i < result.length; i++) {
                            var row = table.insertRow(i);
                            var cell = row.insertCell(0);
                            cell.innerHTML = result[i];
                        }
                    } else {
                        self.input.el.nextSibling.style.display = 'none';;
                    }
                });
        } else {
            this.env.model.dialog.add(AlertDialog, {
                body: _t("Only Supported for 'char' type please change field type to 'char'"),
            });
            return false;
        }
    }
    /*
    *Function to add data to the input field from the table which will
    display values
    */
    _onTableRowClicked(ev) {
        this.input.el.value = ev.target.textContent;
        this.input.el.nextSibling.style.display = 'none';
    }
}
FieldAutoFill.props = {
    ...standardFieldProps,
    value: { type: Function, optional: true },
}
export const Fieldautofill = {
    component: FieldAutoFill,
    supportedTypes: ["char"],
};
registry.category("fields").add("auto_fill", Fieldautofill);
