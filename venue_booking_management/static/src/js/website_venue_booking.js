odoo.define('venue_booking_management.website_page', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc');
    publicWidget.registry.VenueBookingWidget = publicWidget.Widget.extend({
    //Extends the publicWidget.Widget class to hide and show the button and calculate the distance between locations.
        selector: '.venue-booking-widget',
        events: {
            'click #check': '_onCheckClick',
            'click #next': '_onNextClick',
        },
        _onCheckClick: function(ev) {//Click function to fetch from and to location value and calculate the distance.
            var self = this
            var location = this.el.querySelector('#location').value
            if (location!='')
            {
                this.el.querySelector('#loader').classList.remove("d-none");
                ajax.jsonRpc('/geo/' + location , 'call', {
                }).then(function (data) { // success callback
                    self.el.querySelector('#loader').classList.add("d-none");
                    self.el.querySelector('#details').classList.remove("d-none");
                }).catch(function (data) {
                    self.el.querySelector('#loader').classList.add("d-none");
                    Dialog.alert(this, "Please enter valid city");
                    return false;
                });
            }
            else
            {
                Dialog.alert(this, "Add a City");
                return false;
            }
        },
        _onNextClick: function (ev) {//Function to show the customer
//        details form view
            var self = this
            var start_date = self.$el.find('#from_date').val();
            var end_date = self.$el.find('#to_date').val();
            var venue_type = self.$el.find('#venue_type').val();
            var domain = [
                ['start_date', '<', end_date],
                ['end_date', '>', start_date],
                ['venue_id', '=', venue_type],
            ];
            const message = this._rpc({
                model: 'venue.booking',
                method : 'get_booking_dates',
                args: [,start_date, end_date, parseInt(venue_type)],
            }).then(function (data) {
                 if (data['date_result'] == 1){
                     Dialog.alert(self, ("Start date must be less than End date"), {
                            title: ("Error"),
                            confirm_callback: function() {
                            },
                     });
                 }
                 if (data["result"] == 1){
                    Dialog.alert(self, ("Venue is not available for the selected time range."), {
                        title: ("Error"),
                        confirm_callback: function() {
                        },
                    });
                 }
                if (data["date_result"] == 0 && data['result'] == 0){
                    self.el.querySelector('#customer').classList.remove("d-none");
                }
            });
        },
    });
    return publicWidget.registry.VenueBookingWidget;
});
