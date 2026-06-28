/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { _t } from "@web/core/l10n/translation";
import { Component,useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Dialog } from "@web/core/dialog/dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { rpc } from "@web/core/network/rpc";

export class FieldAutoFill extends Component {
    /**
     * Define the template for the DatePickerField component.
     * The template name should match the one used in the XML template.
     */
    static template = 'FieldAutoFill'
    setup() {
        super.setup();
        this.orm = useService("orm");
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
    }
    /**
     *Its a keyup function which will display the values according to key
     *pressed
     */
    _onKeyup(ev) {
        var value = ev.target.value;
        var model = this.env.model.env.searchModel.resModel
        var self = this;
        var values = this.__owl__.props.record._config.fields
        for (const key in values) {
          if (values.hasOwnProperty(key)) {
            if (values[key].name == this.props.name){
                this.props.type = values[key].type
            }
          }
        }
        if(this.props.type === "char") {
            rpc('/matching/records',{
                    model: model,
                    field: this.props.name,
                    value: value,
                })
                .then(function(result) {
                    if(result.length > 0) {
                        self.input.el.nextSibling.style.display = 'block';
                        var table = self.input.el.nextSibling;
                        var i;
                        for(i = 0; i < result.length; i++) {
                                    // Check if the result[i] is already present in the table
                        var isPresent = false;
                        var rows = table.getElementsByTagName('tr');
                        var item = result[i][0];
                        for (var j = 0; j < rows.length; j++) {
                            if (rows[j].cells[0].innerHTML === item) {
                                isPresent = true;
                                break; // Exit loop if match found
                            }
                        }
                        // If not present, create a new row
                        if (isPresent === false) {
                            var row = table.insertRow();
                            var cell = row.insertCell(0);
                            cell.innerHTML = result[i];
                        }
                        }
                    } else {
                        self.props.value = value
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
        this.props.value     = ev.target.textContent;
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
