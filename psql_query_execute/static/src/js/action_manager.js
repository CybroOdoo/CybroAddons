/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

/**
 * XLSX Report Handler
 * This handler is responsible for generating XLSX reports.
 * It sends a request to the server to generate the report in XLSX format
 * and downloads the generated file via /xlsx_reports.
 *
 * @param {Object} action - The action object containing the report details.
 * @returns {Promise<boolean>} - Resolves to true when the report action is handled.
 */
registry.category("ir.actions.report handlers").add("xlsx_handler", async (action) => {
    if (action.report_type === "xlsx") {
        await download({
            url: "/xlsx_reports",
            data: action.data,
        });
        return true;
    }
});
