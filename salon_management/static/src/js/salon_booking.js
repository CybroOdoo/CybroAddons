odoo.define('website_salon_booking_system', function (require) {
'use strict';
var ajax = require('web.ajax');
$(document).on('click',"#submit_button",function() {
   var name = $( "#name" ).val();
   var date = $( "#date" ).val();
   var phone = $( "#phone" ).val();
   var email = $( "#email" ).val();
   var service = $( "#service" ).val();
   var chair = $( "#chair" ).val();
   if (name != "" && date != "" && phone != "" && email != "" && service != "" && chair != "")
   {
   var booking_record = [name, date, phone, email, service, chair];
   var salon_record = ajax.jsonRpc("/page/salon_details", 'call', {'salon_data':booking_record })
            .then(function(){
            window.location= "/page/salon_management.salon_booking_thank_you"
             })
   }
   else
   {
   alert("Fill all the required fields")
   }
});

$(document).on('click',"#check_button",function() {
   var check_date = $( "#check_date" ).val();
   var salon_check_date = ajax.jsonRpc("/page/salon_check_date", 'call', {'check_date':check_date })
                .then(function(date_info){
                window.location= "/page/salon_management.salon_booking_form?x=" + date_info
             })
});
});


