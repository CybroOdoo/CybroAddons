odoo.define('user_audit.AuditBasicController', function (require) {
"use strict";

var core = require('web.core');
var BasicController = require('web.BasicController');
var rpc = require('web.rpc');
var Dialog = require('web.Dialog');

var _t = core._t;

var AuditBasicController = BasicController.include({
//  for managing delete operation
    _deleteRecords: function (ids) {
        var resId;
        if (this.viewType == 'list'){
             resId = this.getSelectedRecords()[0].data.id
        }
        else {
            resId = this.renderer.state.data.id
        }
        var self = this
        function doIt() {
            var resModel = self.modelName
            rpc.query({
                    model: 'user.audit',
                    method: 'create_audit_log_for_delete',
                    args: [resModel,resId],
                }).then(function(data) {
                    })
            return self.model
                .deleteRecords(ids, self.modelName)
                .then(self._onDeletedRecords.bind(self, ids));
        }
        if (this.confirmOnDelete) {
            const message = ids.length > 1 ?
                            _t("Are you sure you want to delete these records?") :
                            _t("Are you sure you want to delete this record?");
            let dialog;
            const confirmCallback = () => {
                doIt().guardedCatch(() => dialog.destroy());
            };
            dialog = Dialog.confirm(this, message, { confirm_callback: confirmCallback });
        } else {
            doIt();
        }
    }

})
return BasicController
})




