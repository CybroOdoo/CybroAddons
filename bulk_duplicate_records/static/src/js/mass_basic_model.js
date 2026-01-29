odoo.define('mass_duplicate_records.BasicModel', function(require) {
    "use strict";

    var BasicModel = require('web.BasicModel');
    var session = require('web.session');
    var BasicModel = BasicModel.include({

        duplicateRecords: function(recordIds, modelName) {
            var self = this;
            var records = _.map(recordIds, function(id) {
                return self.localData[id];
            });
            var context = _.extend(records[0].getContext(), session.user_context);
            for (var i = 0; i < records.length; i++) {
                var new_records = this._rpc({
                    model: modelName,
                    method: 'copy',
                    args: [records[i].res_id],
                    context: context,
                })
            }
            location.reload()
            return new_records
        },
    });
});