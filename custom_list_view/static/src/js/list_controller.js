/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { download } from "@web/core/network/download";
import { rpc } from "@web/core/network/rpc";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ListController.prototype, {
    /**
     * Return the visible columns of the list as export fields.
     *
     * @param {boolean} withTypes also return the store and type of the
     *     fields, as expected by the standard export routes
     * @returns {Object[]}
     */
    _getExportFields(withTypes = false) {
        return this.props.archInfo.columns
            .filter(
                (col) =>
                    (col.optional === false || col.optional === "show") &&
                    col.invisible !== "True"
            )
            .map((col) => this.props.fields[col.name])
            .map((field) => {
                const exportField = {
                    name: field.name,
                    label: field.label || field.string,
                };
                if (withTypes) {
                    exportField.store = field.store;
                    exportField.type = field.field_type || field.type;
                }
                return exportField;
            });
    },

    /**
     * Return the parameters of the list data routes.
     *
     * @returns {Promise<Object>}
     */
    async _getListDataParams() {
        const resIds = await this.model.root.getResIds(true);
        return {
            model: this.model.root.resModel,
            res_ids: resIds.length > 0 ? resIds : false,
            fields: this._getExportFields(),
            domain: this.model.root.domain,
            context: this.props.context,
        };
    },

    /**
     * Show a dialog with the given title and message.
     *
     * @param {string} title
     * @param {string} body
     */
    _showListAlert(title, body) {
        this.dialogService.add(AlertDialog, {
            title,
            body,
            confirmLabel: _t("OK"),
        });
    },

    /**
     * Handle the click event for exporting data to a PDF.
     */
    async _onClickPDF() {
        const params = await this._getListDataParams();
        const lengthField = Array.from(Array(params.fields.length).keys());
        // Retrieve the data for the report
        const data = await rpc("/get_data", params);
        // Generate and download the PDF report
        return this.model.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "custom_list_view.print_pdf_listview",
            report_file: "custom_list_view.print_pdf_listview",
            data: {
                length: lengthField,
                record: data,
            },
        });
    },

    /**
     * Download the list with one of the standard export routes.
     *
     * @param {string} url `/web/export/xlsx` or `/web/export/csv`
     */
    async _downloadListExport(url) {
        const resIds = await this.model.root.getResIds(true);
        await download({
            data: {
                data: JSON.stringify({
                    import_compat: false,
                    context: this.props.context,
                    domain: this.model.root.domain,
                    fields: this._getExportFields(true),
                    groupby: this.model.root.groupBy,
                    ids: resIds.length > 0 && resIds,
                    model: this.model.root.resModel,
                }),
            },
            url,
        });
    },

    /**
     * Handle the click event for exporting data to Excel.
     */
    async _onClickExcel() {
        await this._downloadListExport("/web/export/xlsx");
    },

    /**
     * Handle the click event for exporting data to CSV.
     */
    async _onClickCSV() {
        await this._downloadListExport("/web/export/csv");
    },

    /**
     * Copy the text to the clipboard, using a temporary textarea when the
     * clipboard API is not available.
     *
     * @param {string} text
     * @returns {Promise<boolean>} whether the text was copied
     */
    async _copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            try {
                await navigator.clipboard.writeText(text);
                return true;
            } catch (error) {
                console.warn("Clipboard error:", error);
                return false;
            }
        }
        const textarea = document.createElement("textarea");
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        let copied = false;
        try {
            copied = document.execCommand("copy");
        } catch (error) {
            console.warn("Fallback clipboard copy failed:", error);
        }
        document.body.removeChild(textarea);
        return copied;
    },

    /**
     * Handle the click event for copying data to the clipboard.
     */
    async _onClickCopy() {
        const params = await this._getListDataParams();
        const data = await rpc("/get_data/copy", params);
        // Convert to tab-separated text
        const recText = data.map((record) => record.join("\t")).join("\n");
        if (await this._copyToClipboard(recText)) {
            this._showListAlert(_t("Copied!"), _t("Records copied to clipboard."));
        } else {
            this._showListAlert(_t("Failed"), _t("Clipboard copy failed."));
        }
    },
});
