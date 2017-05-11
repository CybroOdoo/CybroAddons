odoo.define('salon_management.website_salon_booking_system', function (require) {
'use strict';
var ajax = require('web.ajax');
var base = require('web_editor.base');
var core = require('web.core');
var _t = core._t;
$(document).on('click',"#submit_button",function() {
   var name = $( "#name" ).val();
   var date = $( "#date" ).val();
   var time = $( "#time" ).val();
   var phone = $( "#phone" ).val();
   var email = $( "#email" ).val();
   var service = $( "#service" ).val();
   var chair = $( "#chair" ).val();
   var list_service = [];
   var number = service.length
   for (var i=0; i<(service.length); i++){
    var k = {i : service[i]}
    list_service.push(k)
   }
   var time_left_char = time.substring(0, 2)
   var time_right_char = time.substring(3, 5)
   var time_separator = time.substring(2,3)
   if(date != ""){
       if (isNaN(time_left_char) || isNaN(time_right_char) || time_separator != ":"){
           if(time != ""){
           alert("Select a valid Time")
           }
       }
       else{
           var time_left = parseInt(time_left_char)
           var time_right = parseInt(time_right_char)
           if ((time_left < 24) && (time_right < 60) && (time_left >= 0) && (time_right >= 0)){
                if (name != "" && phone != "" && email != "" && service != "" && chair != ""){
                   var booking_record = {'name': name, 'date': date, 'time': time, 'phone': phone,
                    'email': email, service, 'list_service':list_service,'chair': chair,'number': number }
                   $.ajax({
                    url: "/page/salon_details",
                    method: "POST",
                    dataType: "json",
                    data: booking_record,
                    success: function( data ) {
                        window.location.href = "/page/salon_management.salon_booking_thank_you";
                    },
                    error: function (error) {
                    alert('error: ' + error);
                    }
                    });
                }
                else{
                   alert("Fill all the required fields")
                   }
           }
           else {
                alert("Select a valid time")
           }
       }
   }
});
$(document).on('click',"#check_button",function() {
   var check_date = $( "#check_date" ).val();
   if (check_date != "")
       {
       var salon_check_date = ajax.jsonRpc("/page/salon_check_date", 'call', {'check_date':check_date })
                    .then(function(date_info){
                    window.location= "/page/salon_management.salon_booking_form?x=" + date_info
                 })
       }
   else
       {
       alert("Fill the Field")
       }
});
});