/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
/** Extends publicWidget to define button click functions.**/
publicWidget.registry.SalonManagement = publicWidget.Widget.extend({
    selector: '.chair_booking',
    events: {
        'click #send_button': 'ClickSend',
        'click #check_button': 'ClickCheckButton',
    },
    /** Function to check validation cases and create booking
        while click send button from booking page(website). **/
    ClickSend(ev) {
        var name = this.$el.find("#name")[0].value;
        var date = this.$el.find("#date")[0].value;
        var time = this.$el.find("#time")[0].value;
        var phone = this.$el.find("#phone")[0].value;
        var email = this.$el.find("#email")[0].value;
        var service = this.$el.find('.check_box_salon:checkbox:checked');
        var chair = this.$el.find("#chair")[0].value;
        var list_service = [];
        var number = service.length;
        for (var item = 0; item < (number); item++) {
            var value = {item: service[item].attributes['service-id'].value};
            list_service.push(value);
        }
        if (name == "" || date == "" || time == "" || phone == "" || email == "" || list_service.length == 0) {
            alert("All fields are mandatory");
        } else {
        var colonIndex = time.indexOf(":"); // Find the index of ":"
        var hours = time.substring(0, colonIndex);
        var minutes = time.substring(colonIndex + 1)
        var colon = time[colonIndex];
        if (isNaN(hours) || isNaN(minutes) || colon != ':') {
            alert("Select a valid Time");
        } else {
            var time_left = parseInt(hours);
            var time_right = parseInt(minutes);;
                if ((time_left < 25) && (time_right < 60) && (time_left >= 0) && (time_right >= 0)) {
                    jsonrpc('/page/salon_details', {
                        name: name,
                        date: date,
                        salon_time: time,
                        phone: phone,
                        email: email,
                        chair: chair,
                        number: number
                    }).then( function(result){
                    if (JSON.parse(result).result == true){
                        window.location.href = "/page/salon_management/salon_booking_thank_you";
                    }
                    });
                    }
                 else {
                    alert("Select a valid time");
                }
            }
        }
    },
    /** Website function to check already booked chairs and details **/
    ClickCheckButton(ev){
        var check_date = this.$el.find("#check_date").val();
        if (check_date != "") {
            jsonrpc('/page/salon_check_date', {
                check_date
            }).then( function(order_details){
                var x;
                var total_orders = "";
                var order = "";
                var chair_name;
                for (x in order_details) {
                    var chair_name = order_details[x]['name']
                    var i;
                    var lines = "";
                    for (i = 0; i < order_details[x]['orders'].length; i++) {
                        lines += '<tr><td><span>' + order_details[x]['orders'][i]['number'] +
                            '</span></td><td><span>' + order_details[x]['orders'][i]['start_time_only'] +
                            '</span></td><td><span>' + order_details[x]['orders'][i]['end_time_only'] + '</span></td></tr>'
                    }
                    order += '<div class="col-lg-4 s_title pt16 pb16"><div style="height: 200px!important; text-align: center;' +
                        'border: 1px solid #666;padding: 15px 0px;box-shadow: 7px 8px 5px #888888;background-color:#7c7bad;border-radius:58px;color:#fff;margin-bottom: 10px;">' +
                        '<span style="font-size: 15px;">' + chair_name + '</span>' +
                        '<br/><a style="color:#fff;font-size:15px;">Order Details</a>' +
                        '<div id="style-2" style="overflow-y:scroll;height:105px;padding-right:25px;padding-left:25px;margin-right:10px;">' +
                        '<table class="table"><th style="font-size:11px;">Order No.</th><th style="font-size:11px;">Start Time</th>' +
                        '<th style="font-size:11px;">End Time</th><div><tbody style="font-size: 10px;">' +
                        lines + '</tbody></div></table></div></div></div>'
                }
                total_orders += '<div id="booking_chair_div" class="col-lg-12 s_title pt16 pb16 row">' + order + '</div>'
                var res = document.getElementById('booking_chair_div')
                res.innerHTML = "";
                res.innerHTML = total_orders;
                var date_value = 'DATE : <t>' + check_date + '</t>'
                var date_field = document.getElementById('searched_date')
                date_field.innerHTML = "";
                date_field.innerHTML = date_value;
            })
        } else {
            alert("Fill the Field");
        }
    }
});
