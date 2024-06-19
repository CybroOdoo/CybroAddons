odoo.define('vehicle_subscription.subscription_submit_request', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
const ajax = require('web.ajax');
//To getitem  to get vehicle.
$(function() {
               if (localStorage.getItem('current_vehicle')) {
                  $('#current_vehicle').val(localStorage.getItem('current_vehicle'));
              }
});
publicWidget.registry.Request = publicWidget.Widget.extend({
    selector: '.submit_boolean_on',
    start: function() {
    var self = this;//setitem  to store the element.
    var current_vehicle = self.$('#current_vehicle').val();
    localStorage.setItem('current_vehicle', current_vehicle);
       }
})
})
