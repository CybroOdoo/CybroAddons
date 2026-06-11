/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

// Extend public widget to add the total amount for the service
publicWidget.registry.WebsiteFleetServiceWidget = publicWidget.Widget.extend({
    selector: '.website_fleet_service_widget',
    events: {
        'change #service_type': function(ev) {
            var selectedOption = $(ev.target.options[ev.target.selectedIndex]);
            var amount = selectedOption.attr('amount');
            this.$('#amount').val(amount);
        },
    },
});
