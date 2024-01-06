/** @odoo-module */

// Import required modules from the Odoo web framework
import { registry } from "@web/core/registry";
import framework from 'web.framework';
import session from 'web.session';

// Register a handler for generating XLSX reports
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url: '/survey_xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            error: (error) => this.call('crash_manager', 'rpc_error', error),
            complete: framework.unblockUI,
        });
        return def;
    }
});
