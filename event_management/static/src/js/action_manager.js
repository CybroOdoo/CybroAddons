/** @event_management/static/src/js/action_manager.js **/
import { registry } from "@web/core/registry";
import { BlockUI, unblockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";

const reportHandlers = registry.category("ir.actions.report handlers");

if (reportHandlers.contains("xlsx")) {
    reportHandlers.remove("xlsx");
}
reportHandlers.add("xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        BlockUI;
        await download({
            url: '/event_xlsx_reports',
            data: action.data,
            complete: () => unblockUI,
            error: (error) => {
                // Use Odoo's crash manager properly if in OWL context
                const env = owl.Component.env;
                if (env && env.services && env.services.crash_manager) {
                    env.services.crash_manager.rpc_error(error);
                }
            },
        });
    }
});