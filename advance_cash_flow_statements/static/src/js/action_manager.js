/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

// This function is responsible for generating and downloading an XLSX report.
registry.category("ir.actions.report handlers").add("advance_cash_flow_statements_xlsx", async function (action, options, env) {
    if (action.report_type === 'xlsx') {
        env.services.ui.block();
        try {
            await download({
                url: '/cash_flow_xlsx_reports',
                data: action.data,
            });
        } finally {
            env.services.ui.unblock();
        }
        return true;
    }
});
