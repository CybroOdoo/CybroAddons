/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";

 publicWidget.registry.PackersAndMoversWidget = publicWidget.Widget.extend({
    //Extends the publicWidget.Widget class to hide and show the button and calculate the distance between locations.
        selector: '.packers-and-movers-widget',
        events: {
            'click #check': '_onCheckClick',
            'click #next': '_onNextClick',
        },

        _onCheckClick(ev) {//Click function to fetch from and to location value and calculate the distance.
            var self = this
            var from_location = this.el.querySelector('#from').value
            var to_location = this.el.querySelector('#to').value
            if (from_location!='' && to_location!='')
            {
            this.el.querySelector('#loader').classList.remove("d-none");
            jsonrpc('/geo/'+ from_location + '/' +  to_location, {
                        }).then(function(data){ // success callback
                        self.$('#distance').val(data);
                        self.el.querySelector('#loader').classList.add("d-none");
                        self.el.querySelector('#details').classList.remove("d-none");
            }).catch(function (data) {
                self.el.querySelector('#loader').classList.add("d-none");
                alert("Please enter valid city");
                return false;
            });
            }
            else
            {
                alert("Add Pickup city and drop City");
                return false;
            }
        },
        _onNextClick: function (ev) {//Function to show the customer details form view
            this.el.querySelector('#customer').classList.remove("d-none");
        },
    });

