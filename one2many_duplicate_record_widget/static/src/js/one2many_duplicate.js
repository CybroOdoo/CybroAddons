/** @odoo-module */
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";
console.log("first load")
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
export class DuplicateX2ManyField extends X2ManyField {
        setup() {
                super.setup();
                this.orm = useService("orm");
                 X2ManyField.components = {ListRenderer: DuplicateListRenderer };
            }
    get hasSelected(){
        return this.list.records.filter((rec) => rec.selected).length
    }

    async DuplicateRecord(ev){
    let selectedRecords = this.list.records.filter((rec) => rec.selected)
        // Duplicating selected options
        var model = this.field.relation;
        var records = this.list.records;
        var resModel = this.props.record.resModel;
        var field = this.props.name;
        var relation_field = this.field.relation_field;
        var selected_values = []
        for (var i = 0; i < records.length; i++) {
            if (records[i].selected == true){
            console.log("recorde id",records[i].evalContext.active_id)
                selected_values.push(records[i].evalContext.active_id);
            }
        }
        await this.orm.call(
            'duplicate.record',
            'action_duplicate_records',
           [{'values': selected_values, 'resModel': resModel,
                    'field': field, 'relation_field': relation_field,
                    'model': model}],
        ).then((result) =>{
            location.reload();
        });
    }
}
export const O2manyMultiDelete = {
    ...x2ManyField,
    component: DuplicateX2ManyField,
};
DuplicateX2ManyField.template = "one2many_duplicate_record_widget.One2manyDuplicate";
registry.category("fields").add("one2many_duplicate", O2manyMultiDelete);
