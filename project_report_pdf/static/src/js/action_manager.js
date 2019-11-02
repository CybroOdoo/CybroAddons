odoo.define('project_report_pdf.action_manager', function (require) {
"use strict";
/**
 * The purpose of this file is to add the actions of type
 * 'ir_actions_xlsx_download' to the ActionManager.
 */

var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');


ActionManager.include({

    /**
     * Executes actions of type 'ir_actions_xlsx_download'.
     *
     * @private
     * @param {Object} action the description of the action to execute
     * @returns {Deferred} resolved when the report has been downloaded ;
     *   rejected if an error occurred during the report generation
     */
    _executexlsxReportDownloadAction: function (action) {
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url: '/xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            complete: framework.unblockUI,
        });
        return def;
    },
    /**
     * Overrides to handle the 'ir_actions_xlsx_download' actions.
     *
     * @override
     * @private
     */
    _handleAction: function (action, options) {
        if (action.type === 'ir_actions_xlsx_download') {
            return this._executexlsxReportDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    },
});

});
