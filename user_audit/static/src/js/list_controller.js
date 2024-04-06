odoo.define('user_audit.AuditListController', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');
var rpc = require('web.rpc');


var AuditListController = ListController.include({

    custom_events: _.extend({}, ListController.prototype.custom_events, {
        open_record: '_onOpenRecord',
    }),

    // For tracking create operation
    _onCreateRecord: function (ev) {
        this._super();
        var resModel = this.modelName;
        if (this.editable && !state.groupedBy.length) {
            this._addRecord(this.handle);
        } else {
            rpc.query({
                    model: 'user.audit',
                    method: 'create_audit_log_for_create',
                    args: [resModel],
                }).then(function(data) {
                    })
            this.trigger_up('switch_view', {view_type: 'form', res_id: undefined});
        }
    },

    // For tracking read operation
    _onOpenRecord: function(ev) {
        this._super(ev);
        var resModel = this.modelName;
        var record = this.model.get(ev.data.id, {raw: true})
        var resId = record.res_id
        rpc.query({
            model: 'user.audit',
            method: 'create_audit_log_for_read',
            args: [resModel,resId],
        }).then(function(data) {
        })
    },

})
return AuditListController;
})
