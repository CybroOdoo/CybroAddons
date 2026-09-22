/** @odoo-module */
import { useSubEnv } from "@odoo/owl";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { Pager } from "@web/core/pager/pager";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class O2MListRenderer extends ListRenderer {
    setup() {
        super.setup();
        useSubEnv({
            shouldCollapse: this.env.shouldCollapse || (() => false),
        });
    }

    /** Replace the existing function to show selection in the One2many field
         when delete possible **/

    get hasSelectors() {
        const allowSelectors = this.props.allowSelectors || this.props.activeActions?.delete;
        return !!(allowSelectors && !this.env.isSmall);
    }

    get canSelectRecord() {
        return super.canSelectRecord && this.props.list.records.length > 0;
    }

    toggleSelection() {
        if (!this.canSelectRecord) {
            return;
        }
        const list = this.props.list;
        const allSelected = list.records.every(rec => rec.selected);

        for (const record of list.records) {
            record.toggleSelection(!allSelected);
        }
    }

    get selectAll() {
        const records = this.props.list.records;
        if (!records.length) {
            return false;
        }
        return records.every((r) => r.selected);
    }

}

export class TestX2ManyField extends X2ManyField {

    static components = {
        ...X2ManyField.components,
        Pager,
        KanbanRenderer,
        ListRenderer: O2MListRenderer,
    };
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    }
    get hasSelected() {
        return this.list.records.filter((rec) => rec.selected).length
    }
    //Function to delete all the selected records
    async deleteSelected() {
        var w_response = confirm("Do You Want to Delete ?");
        if (w_response) {
            let selected = this.list.records.filter((rec) => rec.selected)
            if (selected[0].evalContext.state == 'sale') {
                this.dialog.add(AlertDialog, {
                    body: _t("Can't able to delete order lines from the confirmed orders"),
                });
            }
            else {
                selected.forEach((rec) => {
                    this.list.delete(rec)
                })
            }
        }
    }
    //Function to delete all the unselected records
    async deleteUnelected() {
        var w_response = confirm("Do You Want to Delete all Unselected");
        if (w_response) {
            let unselected = this.list.records.filter((rec) => !rec.selected)
            unselected.forEach((rec) => {
                this.list.delete(rec)
            })
        }
    }
}

TestX2ManyField.template = "One2manyDelete";
export const oo = {
    ...x2ManyField,
    component: TestX2ManyField,
};
registry.category("fields").add("one2many_delete", oo);
