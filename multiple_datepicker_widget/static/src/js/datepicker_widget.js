/** @odoo-module **/
import basicFields from 'web.basic_fields';
import fieldRegistry from 'web.field_registry';

var FieldDateMultipleDate = basicFields.InputField.extend({
    template: 'FieldDateMultipleDate',
    events: _.extend({}, basicFields.InputField.prototype.events, {
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

fieldRegistry.add('multiple_datepicker', FieldDateMultipleDate);
return {
    FieldDateMultipleDate: FieldDateMultipleDate
};


