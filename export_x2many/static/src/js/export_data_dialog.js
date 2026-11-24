/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
import { GroupBySheetDialog } from "./groupby_sheet_dialog";

/**
 * Extends ExportDataDialog with two additional features:
 *   1. Child-field auto-selection — when "Select child fields" is checked,
 *      adding a relational field to the export list automatically includes its
 *      direct children (and optionally all nested descendants).
 *   2. Multisheet XLSX export — when "Enable data grouping" is checked and
 *      the selected format is XLSX, the export opens a GroupBySheetDialog that
 *      lets the user define per-sheet domain filters before downloading.
 */
patch(ExportDataDialog.prototype, {
    setup() {
        super.setup();
        this.state.includeChildren = false;
        this.state.includeRelatedChildren = false;
        this.state.groupData = false;
        this.state.groupField = "";
    },

    /**
     * Toggle whether direct child fields are auto-selected when a field is added.
     * @param {boolean} value
     */
    onToggleIncludeChildren(value) {
        this.state.includeChildren = value;
    },

    /**
     * Toggle whether nested (related) child fields are also auto-selected.
     * Only meaningful when includeChildren is true.
     * @param {boolean} value
     */
    onToggleIncludeRelatedChildren(value) {
        this.state.includeRelatedChildren = value;
    },

    /**
     * Toggle whether the multisheet grouping dialog should be shown on export.
     * @param {boolean} value
     */
    onToggleEnableGroup(value) {
        this.state.groupData = value;
    },

    /**
     * Recursively collect child fields for a given field ID.
     * When includeRelatedChildren is true all descendants are included;
     * otherwise only the direct children are returned.
     * @param {string} fieldId
     * @returns {Promise<Array>}
     */
    async getAllChildren(fieldId) {
        const field = this.knownFields[fieldId];
        if (!field || !field.children) {
            return [];
        }

        const children = (await this.loadFields(fieldId)) || [];
        let result = [...children];
        if (this.state.includeRelatedChildren === true) {
            for (const child of children) {
                if (child.children) {
                    result.push(...await this.getAllChildren(child.id));
                }
            }
        }

        return result;
    },

    /**
     * Overrides onAddItemExportList to append child fields automatically
     * when the includeChildren state flag is active.
     * @param {string} fieldId
     * @returns {Promise<*|undefined|void>}
     */
    async onAddItemExportList(fieldId) {
        if (!this.state.includeChildren) {
            return super.onAddItemExportList(fieldId);
        }

        const currentField = this.knownFields[fieldId];
        const fields = [currentField];

        if (currentField.children) {
            fields.push(...await this.getAllChildren(fieldId));
        }

        for (const field of fields) {
            if (!this.state.exportList.some((f) => f.id === field.id)) {
                this.state.exportList.push(field);
            }
        }
        this.enterTemplateEdition();
    },

    /**
     * Overrides onClickExportButton to open the multisheet dialog when
     * groupData is enabled and the selected format is XLSX.
     * Falls back to the standard export for all other configurations.
     * @returns {Promise<*|undefined>}
     */
    async onClickExportButton() {
        if (
            !this.state.groupData ||
            this.availableFormats[this.state.selectedFormat].tag !== "xlsx"
        ) {
            return super.onClickExportButton();
        }
        if (!this.state.exportList.length) {
            return this.notification.add(
                _t("Please select fields to save export list..."),
                { type: "danger" }
            );
        }
        return this.dialog.add(GroupBySheetDialog, {
            exportList: this.state.exportList,
            root: this.props.root,
            isCompatible: this.isCompatible,
            onConfirm: () => {},
        });
    },
});
