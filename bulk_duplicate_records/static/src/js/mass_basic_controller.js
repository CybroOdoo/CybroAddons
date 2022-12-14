odoo.define('mass_duplicate_.BasicController', function(require) {
    "use strict";

    var BasicController = require('web.BasicController');
    var menuDuplicateAction = BasicController.include({
        _duplicateRecords: function(ids) {
            var self = this;
            return self.model.duplicateRecords(ids, self.modelName);
        },
    });
});