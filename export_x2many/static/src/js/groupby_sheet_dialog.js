/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { DomainSelector } from "@web/core/domain_selector/domain_selector";
import { _t } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";

/**
 * Dialog component that allows the user to define named filter sheets before
 * performing a multisheet XLSX export.
 *
 * Each sheet entry holds:
 *   - id     {number}  — internal identifier used as the OWL key.
 *   - name   {string}  — worksheet tab label (max 31 chars enforced by Excel).
 *   - domain {string}  — JSON-serialised Odoo domain to filter records.
 */
export class GroupBySheetDialog extends Component {
    static template = "export_x2many.GroupBySheetDialog";
    static components = { Dialog, DomainSelector };
    static props = {
        exportList: Array,
        root: Object,
        close: Function,
        onConfirm: Function,
        isCompatible: Boolean,
    };

    setup() {
        this.state = useState({
            sheets: [
                {
                    id: 1,
                    name: "Sheet 1",
                    domain: "[]",
                },
            ],
            nextId: 2,
            disabled: false,
        });
    }

    /**
     * Append a new blank sheet entry to the sheet list.
     */
    addSheet() {
        this.state.sheets.push({
            id: this.state.nextId++,
            name: `Sheet ${this.state.nextId - 1}`,
            domain: "[]",
        });
    }

    /**
     * Remove a sheet from the list by its identity.
     * @param {{ id: number }} sheet
     */
    removeSheet(sheet) {
        this.state.sheets = this.state.sheets.filter((s) => s.id !== sheet.id);
    }

    /**
     * Update the name of a sheet from an input change event.
     * @param {{ id: number, name: string }} sheet
     * @param {InputEvent} ev
     */
    renameSheet(sheet, ev) {
        sheet.name = ev.target.value;
    }

    /**
     * Sync the domain value emitted by the DomainSelector component.
     * @param {{ id: number, domain: string }} sheet
     * @param {string} domain
     */
    updateDomain(sheet, domain) {
        sheet.domain = domain;
    }

    /**
     * Trigger the multisheet XLSX download.
     * Builds the payload and calls the custom controller route, then closes
     * the dialog and invokes the parent onConfirm callback.
     * @returns {Promise<void>}
     */
    async confirm() {
        const root = this.props.root;
        const exportedFields = this.props.exportList.map((field) => ({
            name: field.name || field.id,
            label: field.label || field.string,
            store: field.store,
            type: field.field_type || field.type,
        }));
        if (this.props.isCompatible) {
            exportedFields.unshift({
                name: "id",
                label: _t("External ID"),
            });
        }
        this.state.disabled = true;
        await download({
            url: `/web/export/xlsx_multisheet`,
            data: {
                data: JSON.stringify({
                    import_compat: this.props.isCompatible,
                    context: root.context,
                    domain: root.domain,
                    fields: exportedFields,
                    groupby: root.groupBy,
                    sheet_list: this.state.sheets,
                    ids:
                        !root.isDomainSelected && root.selection.length
                            ? root.selection.map((e) => e.resId)
                            : false,
                    model: root.resModel,
                }),
            },
        });
        this.state.disabled = false;
        this.props.onConfirm(this.state.sheets);
        this.props.close();
    }
}
