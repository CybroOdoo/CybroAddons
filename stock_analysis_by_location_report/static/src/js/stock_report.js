/** @odoo-module */
/**
 * registers a new handler to generate xlsx report
 */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

const reportHandlers = registry.category("ir.actions.report handlers");
if (!reportHandlers.contains("xlsx")) {
    reportHandlers.add("xlsx", async (action) => {
        if (action.report_type !== "xlsx") {
            return;
        }
        try {
            await download({
                url: "/report_excel",
                data: action.data,
            });
        } catch (error) {
            throw error;
        }
    });
}
