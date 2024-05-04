/** @odoo-module **/
import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
//this is used to call the controller and also passes the report data.
registry.category("ir.actions.report handlers").add("xlsx", async function (action) {
    console.log(action)
    if (action.report_type === 'xlsx') {
        BlockUI;
       await download({
               url: '/xlsx_reports',
               data: action.data,
               complete: () => unblockUI,
               error: (error) => this.call('crash_manager', 'rpc_error', error),
       });
    }
});
