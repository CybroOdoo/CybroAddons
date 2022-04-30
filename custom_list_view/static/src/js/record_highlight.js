odoo.define('custom_list_view.record_highlighted', function (require) {
"use strict";

  var ListRenderer = require("web.ListRenderer");

    ListRenderer.include({

        _onSelectRecord: function (event) {

            var self = this;
            this._super.apply(this, arguments);
            var $selectedRecord = $(event.target).closest('tr')
            if($(event.target).prop('checked')){
                $selectedRecord.addClass('selected_record');
            } else {
                $selectedRecord.removeClass('selected_record')
            }
        },
    });
});
