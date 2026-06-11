/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.PackersAndMoversWidget = publicWidget.Widget.extend({
    selector: '.packers-and-movers-widget',
    events: {
        'click #check': '_onCheckClick',
        'click #next': '_onNextClick',
        "change #country_select": "_onCountryChange",
    },

    _onCheckClick(ev) {
        ev.preventDefault();  // Prevent form submission
        var self = this;
        var from_location = this.el.querySelector('#from').value.trim();
        var to_location = this.el.querySelector('#to').value.trim();
        if (from_location !== '' && to_location !== '') {
            this.el.querySelector('#loader').classList.remove("d-none");
            rpc(`/geo/${from_location}/${to_location}`, {}).then(function(data) {
                if (data) {
                    self.el.querySelector('#distance').value = data;  // Set distance value
                }
                self.el.querySelector('#loader').classList.add("d-none");
                self.el.querySelector('#details').classList.remove("d-none");
            }).catch(function() {
                self.el.querySelector('#loader').classList.add("d-none");
                alert("Please enter a valid city");
            });
        }
        else {
            alert("Add Pickup City and Drop City");
        }
    },

    _onNextClick(ev) {
        ev.preventDefault();  // Prevent form submission
        this.el.querySelector('#details').classList.add("d-none"); // Hide details section
        this.el.querySelector('#customer').classList.remove("d-none"); // Show customer section
    },

     _onCountryChange (ev) {
        var selectedCountryId = ev.target.value;
        var stateSelect = this.$("#state_select");
        stateSelect.find("option").each(function () {
            var option = $(this);
            var countryId = option.data("country");
            if (!countryId || countryId == selectedCountryId) {
                option.show();
            } else {
                option.hide();
            }
        });
     },
});
