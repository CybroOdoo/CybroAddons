odoo.define('manufacturing_reports  .action_manager', function (require) {
"use strict";
/**
 * The purpose of this file is to add the actions of type
 * 'ir_actions_xlsx_download' to the ActionManager.
 */
var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');
ActionManager.include({
    _executexlsxReportDownloadAction: function (action) {
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
    },
    _handleAction: function (action, options) {
        if (action.report_type === 'xlsx') {
            return this._executexlsxReportDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);

},
    });
  });