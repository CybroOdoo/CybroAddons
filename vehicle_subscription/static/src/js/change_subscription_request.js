/** @odoo-module **/

import publicWidget from 'web.public.widget';
import ajax from 'web.ajax';
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
