/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

// This function is responsible for generating and downloading an XLSX report.
registry.category("ir.actions.report handlers").add("stock_xlsx", async (action, options, env) => {
    if (action.report_type === 'stock_xlsx') {
        env.services.ui.block();
        try {
            await download({
                url: '/xlsx_reports',
                data: action.data,
            });
        } catch (error) {
            env.services.notification.add(
                error.message || "An error occurred during the download.",
                { type: "danger" }
            );
        } finally {
            env.services.ui.unblock();
        }
        return true;
    }
});
