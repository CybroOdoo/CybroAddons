odoo.define('attendance.action_manager', function (require) {
"use strict";
/**
* Purpose is to add actions of type
* 'ir.actions.report' to the ActionManager
*/
var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');
ActionManager.include({
 /**
* Executes actions of type 'ir.actions.report'.
*
* @private
* @param {Object} action the description of the action to execute
* @param {Object} options @see doAction for details
* @returns {Promise} resolved when the action has been executed
*/
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
    /**
 * Overrides to handle the 'ir.actions.report' actions.
  *
 * @override
 * @private
   */
    _handleAction: function (action, options) {
        if (action.report_type === 'xlsx') {
            return this._executexlsxReportDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    	},
    });
  });