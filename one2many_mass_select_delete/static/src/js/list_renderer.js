/** @odoo-module */

import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { Pager } from "@web/core/pager/pager";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class O2MListRenderer extends ListRenderer {
    /** Replace the existing function to show selection in the One2many field
         when delete possible **/

    get hasSelectors() {
        if (this.props.activeActions.delete) {
            this.props.allowSelectors = true
        }
        let list = this.props.list
        list.selection = list.records.filter((rec) => rec.selected)
        list.selectDomain = (value) => {
            list.isDomainSelected = value;
            list.model.notify();
        }
        return this.props.allowSelectors && !this.env.isSmall;
    }
 toggleSelection() {
        const list = this.props.list;
        if (!this.canSelectRecord) {
            return;
        }
        if (list.selection.length === list.records.length) {
            list.records.forEach((record) => {
                record.toggleSelection(false);
                list.selectDomain(false);
            });
        } else {
            list.records.forEach((record) => {
                record.toggleSelection(true);
            });
        }
    }
    /** Function that returns if selected any records **/
    get selectAll() {
        const list = this.props.list;
        const nbDisplayedRecords = list.records.length;
        if (list.isDomainSelected) {
          return true;
        }
        else {
          return false
        }
    }
}
export class TestX2ManyField extends X2ManyField {
     setup() {
        super.setup();
        X2ManyField.components = { Pager, KanbanRenderer, ListRenderer: O2MListRenderer };
        this.dialog = useService("dialog");
    }
    get hasSelected(){
        return this.list.records.filter((rec) => rec.selected).length
    }
    //Function to delete all the selected records
    async deleteSelected(){
        var current_model = this.field.relation;
        var w_response = confirm("Do You Want to Delete ?");
        if (w_response){
            let selected = this.list.records.filter((rec) => rec.selected)
            if (selected[0].evalContext.state == 'sale'){
              this.dialog.add(AlertDialog, {
                        body: _t("Can't able to delete order lines from the confirmed orders"),
                        });
            }
            else{
                     selected.forEach((rec) => {
                                    if (this.activeActions.onDelete) {
                                            selected.forEach((rec) => {
                                                    this.activeActions.onDelete(rec);
                                            })
                                    }
                    })
            }
        }
    }
    //Function to delete all the unselected records
    deleteUnselected(){
    console.log('delete unselected')
        var current_model = this.field.relation;
         var w_response = confirm("Do You Want to Delete all Unselected");
         if (w_response){
             let unselected = this.list.records.filter((rec) => !rec.selected)
            var unselected_list =[]
                    unselected.forEach((rec) => {
                            if (this.activeActions.onDelete) {
                                    unselected.forEach((rec) => {
                                            this.activeActions.onDelete(rec);
                                    })
                            }
                    })
        }
    }
}
TestX2ManyField.template = "One2manyDelete";
export const oo = {
    ...x2ManyField,
    component:TestX2ManyField,
};
registry.category("fields").add("one2many_delete", oo);
