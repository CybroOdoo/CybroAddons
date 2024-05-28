/** @odoo-module */
/**
 * registers a new handler to generate xlsx report
 */
import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { session } from "@web/session";
import { download } from "@web/core/network/download";
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
   if (action.report_type === 'xlsx') {
               BlockUI;
       var def = $.Deferred();
       await download({
           url: '/report_excel',
           data: action.data,
           success: def.resolve.bind(def),
           error: (error) => this.call('crash_manager', 'rpc_error', error),
           complete: this.unblockUI,
       });
       return def;
   }
});
