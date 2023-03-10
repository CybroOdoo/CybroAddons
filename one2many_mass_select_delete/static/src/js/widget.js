/** @odoo-module */

import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { ListRenderer } from "@web/views/list/list_renderer";
import {listView} from '@web/views/list/list_view';
import { patch } from "@web/core/utils/patch";
import ajax from 'web.ajax';
import rpc from 'web.rpc';

export class TestListRenderer extends ListRenderer {

  get hasSelectors() {
        this.props.allowSelectors = true
        let list = this.props.list
        list.selection = list.records.filter((rec) => rec.selected)
        list.selectDomain = (value) => {
            list.isDomainSelected = value;
            list.model.notify();
        }
        return this.props.allowSelectors && !this.env.isSmall;
    }
}
export class TestX2ManyField extends X2ManyField {
    get hasSelected(){
        return this.list.records.filter((rec) => rec.selected).length
    }
    async deleteSelected(){

        var current_model = this.field.relation;
        var w_response = confirm("Do You Want to Delete ?");
        if (w_response){
            let selected = this.list.records.filter((rec) => rec.selected)

                this.list.records
                var selected_list =[]
                    selected.forEach((rec) => {
                               if (rec.data.id){
                                    selected_list.push(parseInt(rec.data.id))}
                                else{
                                    if (this.activeActions.onDelete) {
                                            selected.forEach((rec) => {
                                                    this.activeActions.onDelete(rec);
                                            })
                                    }

                                }
                    })
            var self = this;
            if (selected_list.length != 0){
                var response =  await rpc.query({
                                    model: current_model,
                                    method: 'unlink',
                                    args: [selected_list],
                                    }).then(function(response){
                                    self.rendererProps.list.model.load()
                });
                }
        }

    }
    deleteUnselected(){
        var current_model = this.field.relation;
         var w_response = confirm("Do You Want to Select?");
         if (w_response){
             let unselected = this.list.records.filter((rec) => !rec.selected)
            var unselected_list =[]
                    unselected.forEach((rec) => {
                        if (rec.data.id){
                                        unselected_list.push(parseInt(rec.data.id))
                                        }
                        else{
                            if (this.activeActions.onDelete) {
                                    unselected.forEach((rec) => {
                                            this.activeActions.onDelete(rec);
                                    })
                            }

                        }
                    })
            var self = this;
            if (unselected_list.length != 0){
                var response =  rpc.query({
                                    model: current_model,
                                    method: 'unlink',
                                    args: [unselected_list],
                                    }).then(function(response){
                                    self.rendererProps.list.model.load()
                });
            }
        }
    }
}
TestX2ManyField.components = {
    ...X2ManyField.components, ListRenderer: TestListRenderer
};
TestX2ManyField.template = "one2many_mass_select_delete.One2manyDelete";


registry.category("fields").add("one2many_delete", TestX2ManyField);
