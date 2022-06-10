odoo.define('pos_report_generator.action_manager', function (require) {
"use strict";
/**
 * The purpose of this file is to add the actions of type
 * 'xlsx' to the ActionManager.
 */
var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');
ActionManager.include({
    /**
     * Executes actions of type 'ir.actions.report'.
     * @private
     * @param {Object} action the description of the action to execute
     * @param {Object} options @see doAction for details
     * @returns {Promise} resolved when the action has been executed
     */
    _executeposdynamicxlsxReportDownloadAction: function (action) {
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url: '/pos_dynamic_xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            error: (error) => this.call('crash_manager', 'rpc_error', error),
            complete: framework.unblockUI,
        });
        return def;
    },
    /**
     * Overrides to handle the 'ir.actions.report' actions.
     * @override
     * @private
     */
     _handleAction: function (action, options) {

        if (action.type === 'ir_actions_pos_dynamic_xlsx_download') {
            return this._executeposdynamicxlsxReportDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    },
});

});
