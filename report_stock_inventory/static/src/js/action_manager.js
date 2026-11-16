/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

// This function is responsible for generating and downloading an XLSX report.
registry.category("ir.actions.report handlers").add("report_stock_inventory_xlsx", async (action, options, env) => {
    if (action.report_type === "xlsx") {
        env.services.ui.block();
        try {
            await download({
                url: "/xlsx_reports",
                data: action.data,
            });
        } finally {
            env.services.ui.unblock();
        }
        if (options && options.onClose) {
            options.onClose();
        }
        return true;
    }
    return false;
});
