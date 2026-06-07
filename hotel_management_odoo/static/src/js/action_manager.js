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
registry.category("ir.actions.report handlers").add("hotel_xlsx", async function (action, options, env) {
    if (action.report_type === 'xlsx') {
        env.services.ui.block();
        try {
            await download({
                url: '/xlsx_reports',
                data: action.data,
            });
            env.services.ui.unblock();
        } catch (error) {
            env.services.ui.unblock();
            throw error;
        }
        return true;
    }
});
