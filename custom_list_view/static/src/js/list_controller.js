/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from '@web/views/list/list_controller';
import { download } from "@web/core/network/download";
import { rpc } from "@web/core/network/rpc";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ListController.prototype, {
       /**
        * Handle the click event for exporting data to a PDF.
        */
    _onClickPDF: async function() {
        var self = this;
        // Retrieve the fields to export
    const fields = this.props.archInfo.columns
        .filter((col) => (
            (col.optional === false || col.optional === "show") &&
            col.invisible !== "True"
        )).map((col) => this.props.fields[col.name]);
        const exportFields = fields.map((field) => ({
            name: field.name,
            label: field.label || field.string,
        }));
        const resIds = await this.getSelectedResIds();
        var length_field = Array.from(Array(exportFields.length).keys());
        // Make a JSON-RPC request to retrieve the data for the report
        rpc('/get_data', {
            'model': this.model.root.resModel,
            'res_ids': resIds.length > 0 && resIds,
            'fields': exportFields,
            'grouped_by': this.model.root.groupBy,
            'context': this.props.context,
            'domain': this.model.root.domain,
            'context': this.props.context,
        }).then(function(data) {
            var model = self.model.root.resModel
            // Generate and download the PDF report
            return self.model.action.doAction({
                type: "ir.actions.report",
                report_type: "qweb-pdf",
                report_name: 'custom_list_view.print_pdf_listview',
                report_file: "custom_list_view.print_pdf_listview",
                data: {
                    'length': length_field,
                    'record': data
                }
            });
        });
    },
    /**
     * Handle the click event for exporting data to Excel.
     */
    _onClickExcel: async function() {
        // Retrieve the fields to export
    const fields = this.props.archInfo.columns
        .filter((col) => (
            (col.optional === false || col.optional === "show") &&
            col.invisible !== "True"
        )).map((col) => this.props.fields[col.name]);
        const exportFields = fields.map((field) => ({
            name: field.name,
            label: field.label || field.string,
            store: field.store,
            type: field.field_type || field.type,
        }));
        const resIds = await this.getSelectedResIds();
        const import_compat = false
        // Make a request to download the Excel file
        await download({
            data: {
                data: JSON.stringify({
                    import_compat,
                    context: this.props.context,
                    domain: this.model.root.domain,
                    fields: exportFields,
                    groupby: this.model.root.groupBy,
                    ids: resIds.length > 0 && resIds,
                    model: this.model.root.resModel,
                }),
            },
            url: `/web/export/xlsx`,
        });
    },
    /**
     * Handle the click event for exporting data to CSV.
     */
    _onClickCSV: async function() {
    const fields = this.props.archInfo.columns
        .filter((col) => (
            (col.optional === false || col.optional === "show") &&
            col.invisible !== "True"
        )).map((col) => this.props.fields[col.name]);
        const exportFields = fields.map((field) => ({
            name: field.name,
            label: field.label || field.string,
            store: field.store,
            type: field.field_type || field.type,
        }));
        const resIds = await this.getSelectedResIds();
        const import_compat = false
        // Make a request to download the CSV file
        await download({
            data: {
                data: JSON.stringify({
                    import_compat,
                    context: this.props.context,
                    domain: this.model.root.domain,
                    fields: exportFields,
                    groupby: this.model.root.groupBy,
                    ids: resIds.length > 0 && resIds,
                    model: this.model.root.resModel,
                }),
            },
            url: `/web/export/csv`,
        });
    },
    /**
     * Handle the click event for copying data to the clipboard.
     */
    _onClickCopy: async function () {
        const self = this;

        // Step 1: Prepare fields to export
        const fields = this.props.archInfo.columns
            .filter((col) =>
                (col.optional === false || col.optional === "show") &&
                col.invisible !== "True"
            ).map((col) => this.props.fields[col.name]);

        const exportFields = fields.map((field) => ({
            name: field.name,
            label: field.label || field.string,
        }));

        // Step 2: Get selected record IDs
        const resIds = await this.getSelectedResIds();

        // Step 3: Request data from the backend
        rpc('/get_data/copy', {
            model: this.model.root.resModel,
            res_ids: resIds.length > 0 ? resIds : false,
            fields: exportFields,
            grouped_by: this.model.root.groupBy,
            domain: this.model.root.domain,
            context: this.props.context,
        }).then(function (data) {

            // Step 4: Convert to tab-separated text
            const recText = data.map((record) => record.join("\t")).join("\n");

            // Step 5: Copy to clipboard
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(recText).then(() => {
                    self.dialogService.add(AlertDialog, {
                        title: _t('Copied!'),
                        body: _t('Records copied to clipboard.'),
                        confirmLabel: _t('OK'),
                    });
                }).catch((err) => {
                    console.error("Clipboard error:", err);
                    self.dialogService.add(AlertDialog, {
                        title: _t('Failed'),
                        body: _t('Clipboard copy failed.'),
                        confirmLabel: _t('OK'),
                    });
                });
            } else {
                // Fallback: Create a temporary textarea and select/copy
                const textarea = document.createElement("textarea");
                textarea.value = recText;
                document.body.appendChild(textarea);
                textarea.select();
                try {
                    document.execCommand("copy");
                    self.dialogService.add(AlertDialog, {
                        title: _t('Copied!'),
                        body: _t('Records copied to clipboard.'),
                        confirmLabel: _t('OK'),
                    });
                } catch (err) {
                    console.error("Fallback clipboard copy failed:", err);
                }
                document.body.removeChild(textarea);
            }
        });
    },
});
