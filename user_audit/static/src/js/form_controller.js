odoo.define('user_audit.AuditFormController', function (require) {
"use strict";

var core = require('web.core');
var FormController = require('web.FormController');
var rpc = require('web.rpc');

var AuditFormController = FormController.include({
//   For manging save record
    saveRecord: async function () {
         const changedFields = await this._super(...arguments);
         var resModel = this.modelName
         var resId = this.initialState.res_id
         rpc.query({
                    model: 'user.audit',
                    method: 'create_audit_log_for_write',
                    args: [resModel,resId],
                }).then(function(data) {
                    })
         return changedFields
    },

//    For managing create operation
    createRecord: async function (parentID, additionalContext) {
        this._super();
        var resModel = this.modelName
        rpc.query({
                    model: 'user.audit',
                    method: 'create_audit_log_for_create',
                    args: [resModel],
                }).then(function(data) {
                    })
    }
})
return AuditFormController
})
