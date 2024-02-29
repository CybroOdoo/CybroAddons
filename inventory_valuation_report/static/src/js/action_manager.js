/** @odoo-module */
/**
 * @module ir.actions.report handlers
 * @description Contains handlers for generating XLSX reports in Odoo
 */

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import framework from 'web.framework';
import session from 'web.session';

/**
 * Add handler for generating XLSX reports.
 * @param {Object} action - The action object containing report information
 * @returns {Promise} - A Promise that resolves when the report is generated and downloaded
 */
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url: '/xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            error: (error) => this.call('crash_manager', 'rpc_error', error),
            complete: framework.unblockUI,
        });
        return def;
    }
});
