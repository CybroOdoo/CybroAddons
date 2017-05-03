odoo.define('website_salon_booking_system', function (require) {
'use strict';
var ajax = require('web.ajax');
$(document).on('click',"#submit_button",function() {
   var name = $( "#name" ).val();
   var date = $( "#date" ).val();
   var time = $( "#time" ).val();
   var phone = $( "#phone" ).val();
   var email = $( "#email" ).val();
   var service = $( "#service" ).val();
   var chair = $( "#chair" ).val();
   var time_left_char = time.substring(0, 2)
   var time_right_char = time.substring(3, 5)
   var time_separator = time.substring(2,3)
   var date_day = date.substring(3,5)
   var date_month = date.substring(0,2)
   var date_year = date.substring(6,10)
   var slash_one = date.substring(2,3)
   var slash_two = date.substring(5,6)
   if ((date_day < 32) && (date_day > 0) && (date_month < 13) && (date_month > 0) &&
   (date_year > 2016) && (slash_one == "/") && (slash_two == "/")){
        var correct_date = 0
        if([1,3,5,7,8,10,12].indexOf(date_month) == -1){
            if(date_month == 2){
                if((date_year % 4) == 0){
                    if(date_day < 30){
                        correct_date = 1
                    }
                    else{
                        alert("Selected February Has 29 Days Only.")
                    }
                }
                else{
                    if(date_day < 29){
                        correct_date = 1
                    }
                    else{
                        alert("Selected February Has 28 Days Only.")
                    }
                }
            }
            else{
                if(date_day < 31){
                    correct_date = 1
                }
                else{
                    alert("Selected Month Have 30 Days Only")
                }
            }
        }
        else{
            if(date_day < 32){
            correct_date = 1
            }
            else{
            alert("Selected Month Have 31 Days Only")
            }
        }
   }
   else{
    if(date != ""){
       alert("Select a valid Date")
    }
   }
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
                   var booking_record = [name, date, time, phone, email, service, chair];
                   var salon_record = ajax.jsonRpc("/page/salon_details", 'call', {'salon_data':booking_record })
                            .then(function(){
                            window.location= "/page/salon_management.salon_booking_thank_you"
                             })
                }
                else{
                   alert("Fill all the required fields")
                   }
           }
           else{
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