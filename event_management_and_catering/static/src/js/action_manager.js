/** @odoo-module **/
/** Xlsx report action manager */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

/**
 * XLSX Handler - sends request to server to generate XLSX report and downloads it.
 */
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        await download({
            url: '/event_xlsx_reports',
            data: action.data,
        });
        return true;
    }
});
