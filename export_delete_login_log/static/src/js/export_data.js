odoo.define('custom_module.CustomDataExport', function (require) {
    "use strict";
    var DataExport = require('web.DataExport');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var CustomDataExport = DataExport.include({
        async _exportData(exportedFields, exportFormat, idsToExport) {
            // Call the original export function
            this._super.apply(this, arguments);
            const records = this.idsToExport.map(id => ({ rec_id: id, rec_model: this.record.model }));
            // Create the exportList array
            const exportList = this.defaultExportFields.map(field => ({ field_name: field }));
            // Combine into the final result
            const list = {
              records: records,
              exportList: exportList
            };
            rpc.query({
                        model: 'export.log',
                        method: 'action_create_export_log',
                        args: [0, list],
                    })
        },
    });
    return CustomDataExport;
});
