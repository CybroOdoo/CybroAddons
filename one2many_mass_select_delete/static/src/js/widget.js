/** @odoo-module */

import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { ListRenderer } from "@web/views/list/list_renderer";
import {listView} from '@web/views/list/list_view';
import { patch } from "@web/core/utils/patch";

export class TestListRenderer extends ListRenderer {
  get hasSelectors() {
        this.props.allowSelectors = true
        this.props.list.selection = true
        return this.props.allowSelectors && !this.env.isSmall;
    }
    toggleRecordSelection(record) {
        record.toggleSelection();
    }

}
export class TestX2ManyField extends X2ManyField {
    get hasSelected(){
        return this.list.records.filter((rec) => rec.selected).length
    }
    deleteSelected(){
        var w_response = confirm("Dou You Want to Delete ?");
        if (w_response){
            console.log(this.list.records)
            let selected = this.list.records.filter((rec) => rec.selected)
            if (this.activeActions.onDelete) {
                selected.forEach((rec) => {
                        this.activeActions.onDelete(rec);
                })
            }
        }
    }
    deleteUnselected(){
         var w_response = confirm("Dou You Want to Select?");
         if (w_response){
             let unselected = this.list.records.filter((rec) => !rec.selected)
            if (this.activeActions.onDelete) {
                unselected.forEach((rec) => {
                        this.activeActions.onDelete(rec);
                })
            }
        }
    }
}
TestX2ManyField.components = {
    ...X2ManyField.components, ListRenderer: TestListRenderer
};
TestX2ManyField.template = "one2many_mass_select_delete.One2manyDelete";


registry.category("fields").add("one2many_delete", TestX2ManyField);
