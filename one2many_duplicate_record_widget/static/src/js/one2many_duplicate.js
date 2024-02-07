/** @odoo-module */

import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import rpc from 'web.rpc';

export class DuplicateListRenderer extends ListRenderer {

    get hasSelectors() {
        //Add selector option in one2many field
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
export class DuplicateX2ManyField extends X2ManyField {
    get hasSelected(){
        return this.list.records.filter((rec) => rec.selected).length
    }
    async DuplicateRecord(){
        // Duplicating selected options
        var model = this.field.relation;
        var records = this.props.value.records;
        var resModel = this.props.record.resModel;
        var field = this.props.name;
        var relation_field = this.field.relation_field;
        var selected_values = []
        for (var i = 0; i < records.length; i++) {
            if (records[i].selected == true){
                selected_values.push(records[i].data.id)
            }
        }
        rpc.query({
            model: 'duplicate.record',
            method: 'action_duplicate_records',
            args: [[], {'values': selected_values, 'resModel': resModel,
                    'field': field, 'relation_field': relation_field,
                    'model': model}],
        }).then((result) =>{
            location.reload();
        });
    }
}
DuplicateX2ManyField.components = {
    ...X2ManyField.components, ListRenderer: DuplicateListRenderer
};
DuplicateX2ManyField.template = "one2many_duplicate_record_widget.One2manyDuplicate";


registry.category("fields").add("one2many_duplicate", DuplicateX2ManyField);
