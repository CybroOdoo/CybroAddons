odoo.define('multiple_datepicker_widget.MultipleDatePickerWidget', function(require) {
    "use strict";
    var field_registry = require('web.field_registry');
    var fields = require('web.basic_fields');

    var FieldDateMultipleDate = fields.InputField.extend({
        template: 'FieldDateMultipleDate',
        events: _.extend({}, fields.InputField.prototype.events, {
            'click': '_onSelectDateField',
        }),

        _onSelectDateField: function(ev) {
            if (this.$input){
                this.$input.datepicker({
                    multidate: true,
                }).trigger('focus');
            }
        },
    });

    field_registry.add('multiple_datepicker', FieldDateMultipleDate);
    return {
        FieldDateMultipleDate: FieldDateMultipleDate
    };
});


