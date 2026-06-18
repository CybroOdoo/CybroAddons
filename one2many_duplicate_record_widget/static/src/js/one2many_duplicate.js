/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import {
    SaleOrderLineListRenderer,
    SaleOrderLineOne2Many,
    saleOrderLineOne2Many,
} from "@sale/js/sale_order_line_field/sale_order_line_field";

export class DuplicateListRenderer extends SaleOrderLineListRenderer {
    get hasSelectors() {
        return !this.env.isSmall;
    }

    toggleSelection() {
        const list = this.props.list;
        if (list.toggleSelection) {
            return super.toggleSelection();
        }
        // Fallback for StaticList (x2many in form views)
        const allSelected = list.records.every((record) => record.selected);
        for (const record of list.records) {
            record.toggleSelection(!allSelected);
        }
    }
}

export class DuplicateX2ManyField extends SaleOrderLineOne2Many {
    static components = {
        ...SaleOrderLineOne2Many.components,
        ListRenderer: DuplicateListRenderer,
    };
    setup() {
        super.setup();
        this.orm = useService("orm");
    }
    get hasSelected() {
        return this.list.records.some(r => r.selected);
    }
    async DuplicateRecord(ev) {
        var model = this.field.relation;
        var resModel = this.props.record.resModel;
        var field = this.props.name;
        var relation_field = this.field.relation_field;
        var selected_values = [];
        const records = this.list.records;
        for (var i = 0; i < records.length; i++) {
            if (records[i].selected && records[i].evalContext && records[i].evalContext.id) {
                selected_values.push(records[i].evalContext.id);
            }
        }
        await this.orm.call('duplicate.record', 'action_duplicate_records', [{
            'values': selected_values, 'resModel': resModel, 'field': field,
            'relation_field': relation_field, 'model': model
        }]).then((result) => {
            location.reload();
        });
    }
}

export const O2manyMultiDelete = {
    ...saleOrderLineOne2Many,
    component: DuplicateX2ManyField,
    displayName: _t("Duplicate table"),
};

DuplicateX2ManyField.template = "one2many_duplicate_record_widget.One2manyDuplicate";
registry.category("fields").add("one2many_duplicate", O2manyMultiDelete);
