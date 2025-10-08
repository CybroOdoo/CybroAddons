/** @odoo-module **/
/** Xlsx report action manager */
import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
registry.category("ir.actions.report handlers").add("xlsx", async function (action) {
   if (action.report_type === 'low_sale_xlsx_download') {
        BlockUI;
         await download({
         url: '/sale_low_xlsx_reports',
         data: action.data,
         complete: () => unblockUI,
         error: (error) => self.call('crash_manager', 'rpc_error', error),
         });
   }});
