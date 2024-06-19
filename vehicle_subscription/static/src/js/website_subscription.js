odoo.define('vehicle_subscription.subscription', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
const Dialog = require('web.Dialog');
const ajax = require('web.ajax');
publicWidget.registry.Location = publicWidget.Widget.extend({
    selector: '#whole_sub',
    events: {
        'click #location_id': '_onLocationClick',
        'change #state_id':'_onStateChange',
        'click #dismiss':'_onCloseClick',
    },
     _onLocationClick: function (ev) { //function that opens modal
            var location = this.$('#location_temp')[0];
            location.style.display='block';
     },
    _onStateChange:function(ev){ // On the change of state ,city gets changed
           var self=this;
           var state_id = ev.currentTarget.value
           ajax.jsonRpc('/online/subscription/city', "call", {
                    'state': state_id,
           })
            .then(function(result) {
                const select = self.$el.find('#city_id')[0];
                const options = Array.from(select.options);
                    options.forEach((option) => {
                        option.remove();
                    });
                    result.forEach((item) => {
                     let newOption = new Option(item, item);
                        select.add(newOption, undefined);
                    });
            });
         },
      // Click function of close button state and city is appended in location field.
      _onCloseClick: function(ev){
           var location = this.$('#location_temp')[0];
           var city=this.$('#city_id')[0].value
           var state=this.$("#state_id option:selected").data('state-name');
           this.$('#location_id')[0].value = state +','+ city
           location.style.display='none';
      },
    })
})
