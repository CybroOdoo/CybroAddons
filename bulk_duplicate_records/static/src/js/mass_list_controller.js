odoo.define('mass_duplicate_records.mass_duplicate', function(require) {
    "use strict";


    var core = require('web.core');
    const ListController = require('web.ListController');
    var _t = core._t;

    const NewMenuItem = ListController.include({
        _onDuplicateSelectedRecords: function() {
            this._duplicateRecords(this.selectedRecords);
        },
        _getActionMenuItems: function(state) {
            const props = this._super(...arguments);
            const otherActionItems = [];
            if (this.activeActions && props) {
                props.items.other.unshift({
                    description: _t("Mass Duplicate"),
                    callback: () => this._onDuplicateSelectedRecords()
                });
                return props;
            }
        },

    });
});