/** @odoo-module **/
import {registry} from "@web/core/registry";
import {useInputField} from "@web/views/fields/input_field_hook";
const {Component,useRef} = owl;
var ajax = require('web.ajax');
var Dialog = require('web.Dialog');

/**
 * We define this module for getting data from controller and pass to frontend
 *
 */
export class FieldAutoFill extends Component {
    static template = 'FieldAutoFill';
    setup() {
        super.setup();
        this.input = useRef('input_data');
        useInputField({
            getValue: () => this.props.value || "",
            refName: "input_data"
        });
    }
    /**
     *Its a keyup function which will display the values according to key pressed
     */
    _onKeyup(ev) {
        var value = ev.target.value;
        var model = this.env.model.env.searchModel.resModel
        var self=this;
        if(this.props.type === "char") {
            ajax.jsonRpc('/matching/records', 'call', {
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
            Dialog.alert(this,
                "Only Supported for 'char' type please change field type to 'char'")
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

registry.category("fields")
    .add('auto_fill', FieldAutoFill);