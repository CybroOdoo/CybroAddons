/** @odoo-module **/
import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
/**
XLSX Handler
This handler is responsible for generating XLSX reports.
It sends a request to the server to generate the report in XLSX format
and downloads the generated file.
@param {Object} action - The action object containing the report details.
@returns {Promise} - A promise that resolves when the report generation is complete.
*/
registry.category("ir.actions.report handlers").add("xlsx", async function (action) {
    if (action.report_type === 'xlsx') {
        BlockUI;
       await download({
               url: '/xlsx_reports',
               data: action.data,
               complete: () => unblockUI,
               error: (error) => self.call('crash_manager', 'rpc_error', error),
               });
    }
});
