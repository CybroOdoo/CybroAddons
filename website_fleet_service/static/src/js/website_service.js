odoo.define('website_fleet_service.website_service', function(require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    publicWidget.registry.WebsiteFleetServiceWidget = publicWidget.Widget.extend({//Extend public widget to add the total amount for te service
        selector: '.website_fleet_service_widget',
        events: {
            'change #service_type': function(ev) {
            this.$('#amount').val($(ev.target.options[ev.target.selectedIndex]).getAttributes().amount)
            },
        },
    });
    return publicWidget.registry.WebsiteFleetServiceWidget;
});
