/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

// This function is responsible for generating and downloading an XLSX report.
registry.category("ir.actions.report handlers").add("xlsx", async function (action, options, env) {
    if (action.report_type === 'xlsx') {
        if (env && env.services && env.services.ui) {
            env.services.ui.block();
        }
        try {
            await download({
                url: '/xlsx_reports',
                data: action.data,
            });
        } finally {
            if (env && env.services && env.services.ui) {
                env.services.ui.unblock();
            }
        }
        return true;
    }
});

