/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from '@web/views/list/list_controller';
import { download } from "@web/core/network/download";
import { jsonrpc } from "@web/core/network/rpc_service";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ListController.prototype, {
//    /**
//     * Handle the click event for exporting data to a PDF.
//     */
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
        jsonrpc('/get_data', {
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
    _onClickCopy: async function() {
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
        // Make a JSON-RPC request to retrieve the data to copy
        jsonrpc('/get_data/copy', {
            'model': this.model.root.resModel,
            'res_ids': resIds.length > 0 && resIds,
            'fields': exportFields,
            'grouped_by': this.model.root.groupBy,
            'context': this.props.context,
            'domain': this.model.root.domain,
            'context': this.props.context,
        }).then(function(data) {
            // Format the data as text and copy it to the clipboard
            var recText = data.map(function(record) {
                return record.join("\t"); // Join the elements of each array with tabs ("\t")
            }).join("\n");
            // Copy the recText to the clipboard
            navigator.clipboard.writeText(recText);
            self.dialogService.add(AlertDialog, {
            title: _t('Copied !!'),
            body: _t("Records Copied to Clipboard."),
            confirmLabel: _t('Ok'),
        });
        });
    },
});
