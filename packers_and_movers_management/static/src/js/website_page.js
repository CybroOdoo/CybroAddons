odoo.define('packers_and_movers_management.website_page', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    publicWidget.registry.PackersAndMoversWidget = publicWidget.Widget.extend({
    //Extends the publicWidget.Widget class to hide and show the button and calculate the distance between locations.
        selector: '.packers-and-movers-widget',
        events: {
            'click #check': '_onCheckClick',
            'click #next': '_onNextClick',
        },

        _onCheckClick: function(ev) {//Click function to fetch from and to location value and calculate the distance.
            var self = this
            var from_location = this.el.querySelector('#from').value
            var to_location = this.el.querySelector('#to').value
            if (from_location!='' && to_location!='')
            {
                this.el.querySelector('#loader').classList.remove("d-none");
                ajax.jsonRpc('/geo/' + from_location + '/' +  to_location, 'call', {
                }).then(function (data) { // success callback
                    self.$('#distance').val(data);
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
                Dialog.alert(this, "Add Pickup city and drop City");
                return false;
            }
        },
        _onNextClick: function (ev) {//Function to show the customer details form view
            this.el.querySelector('#customer').classList.remove("d-none");
        },
    });
    return publicWidget.registry.PackersAndMoversWidget;
});
