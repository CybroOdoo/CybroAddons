/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import {
    SaleOrderLineListRenderer,
    SaleOrderLineOne2Many,
    saleOrderLineOne2Many,
} from "@sale/js/sale_order_line_field/sale_order_line_field";

export class DuplicateListRenderer extends SaleOrderLineListRenderer {
    setup() {
        super.setup();
        this.uiService = this.uiService || useService("ui");
    }

    get hasSelectors() {
        return !this.uiService.isSmall;
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
        this.action = useService("action");
        this.orm = useService("orm");
        this.ui = useService("ui");
    }

    get hasSelected() {
        return this.list.records.some((r) => r.selected);
    }

    async DuplicateRecord(ev) {
        const left = await this.list.leaveEditMode();
        if (!left) {
            return;
        }
        const selectedRecords = this.list.records.filter((r) => r.selected);
        if (selectedRecords.length === 0) {
            return;
        }

        // Duplicate records directly within the One2Many list context
        if (this.list.duplicateRecords) {
            await this.list.duplicateRecords(selectedRecords);
        } else {
            const selectedIds = selectedRecords
                .filter((r) => r.resId)
                .map((r) => r.resId);

            if (selectedIds.length > 0) {
                await this.orm.call("duplicate.record", "action_duplicate_records", [{
                    values: selectedIds,
                    model: this.field.relation,
                    resModel: this.props.record.resModel,
                    field: this.props.name,
                    relation_field: this.field.relation_field,
                }]);
                // Reload relational data cleanly without browser reload
                await this.props.record.load();
            } else {
                for (const record of selectedRecords) {
                    const data = {};
                    for (const fieldName of Object.keys(record.fields)) {
                        if (
                            fieldName in record.data &&
                            fieldName !== "id" &&
                            !record._isReadonly(fieldName)
                        ) {
                            data[fieldName] = record.data[fieldName];
                        }
                    }
                    await this.list.addNewRecord({ mode: "readonly", data });
                }
            }
        }

        // Deselect records after duplication
        for (const record of this.list.records) {
            if (record.selected) {
                record.toggleSelection(false);
            }
        }
    }
}

export const one2manyDuplicate = {
    ...saleOrderLineOne2Many,
    component: DuplicateX2ManyField,
    displayName: _t("Duplicate table"),
};

// Retain alias for backwards compatibility
export const O2manyMultiDelete = one2manyDuplicate;

DuplicateX2ManyField.template = "one2many_duplicate_record_widget.One2manyDuplicate";
registry.category("fields").add("one2many_duplicate", one2manyDuplicate);
