/** @odoo-module */

import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
/**
 * Handles XLSX report downloads for actions of type 'xlsx'.
 * Sends a request to `/xlsx_reports` with the action data payload
 * and triggers a file download on completion.
 */
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        BlockUI;
        await download({
            url: '/xlsx_reports',
            data: action.data,
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
});
