/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

// This function is responsible for generating and downloading an XLSX report.
registry.category("ir.actions.report handlers").add("venue_xlsx_handler", async (action, options, env) => {
    if (action.report_type === "xlsx") {
        await download({
            url: "/venue_xlsx_reports",
            data: action.data,
        });
        if (options && options.onClose) {
            options.onClose();
        }
        return true;
    }
    return false;
});


