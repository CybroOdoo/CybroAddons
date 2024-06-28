/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import framework from 'web.framework';
import session from 'web.session';
//this is used to call the controller and also passes the report data.
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === 'stock_xlsx') {
        framework.blockUI();
        var self = this;
        var def = $.Deferred();
        session.get_file({
            url: '/xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            error: (error) => self.call('crash_manager', 'rpc_error', error),
            complete: framework.unblockUI,
        });
        return def;
    }
});
