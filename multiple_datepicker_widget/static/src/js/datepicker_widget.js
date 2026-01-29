/** @odoo-module **/
import basicFields from 'web.basic_fields';
import fieldRegistry from 'web.field_registry';
    const field_utils = require('web.field_utils');
    var time = require('web.time');
    var translation = require('web.translation');
    var _t = translation._t;

var FieldDateMultipleDate = basicFields.InputField.extend({
    template: 'FieldDateMultipleDate',
    events: _.extend({}, basicFields.InputField.prototype.events, {
        'click': '_onSelectDateField',
    }),


    _onSelectDateField: function(ev) {
      var dateFormat = time.getLangDateFormat();
      console.log("dateFormat....",dateFormat);
       if (dateFormat.includes('MMMM')){
          var dates = dateFormat.toLowerCase()
          var result = dates.replace(/mmmm/g, 'MM');
          dateFormat = result


      }
      else if (dateFormat.includes('MMM')) {
          var dates = dateFormat.toLowerCase()
          var result = dates.replace(/mmm/g, 'M');
          dateFormat = result

      }
      else if(dateFormat.includes('ddd')){

          var dates = dateFormat.toLowerCase()
          var result = dates.replace(/ddd/g, 'DD');
          dateFormat = result

      }

     else{
        dateFormat = dateFormat.toLowerCase()
     }
        if (this.$input){
            this.$input.datepicker({
                multidate: true,
                format: dateFormat,
            }).trigger('focus');
        }

    },
});
console.log("FieldDateMultipleDate",FieldDateMultipleDate)
fieldRegistry.add('multiple_datepicker', FieldDateMultipleDate);
return {
    FieldDateMultipleDate: FieldDateMultipleDate
};


