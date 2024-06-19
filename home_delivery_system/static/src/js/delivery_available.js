odoo.define('home_delivery_system.available', function (require) {
'use strict';
var publicWidget = require('web.public.widget');
var rpc = require('web.rpc');
publicWidget.registry.DeliveryWidget = publicWidget.Widget.extend({
    selector: ".available",
    events: {
        'click .delivery_available': 'onClickAvailable',
    },
    //When the delivery person accepts the delivery.
    onClickAvailable(ev) {
        var result = rpc.query({
                    model: 'stock.picking',
                    method: 'delivery_available',
                    args: [,],
                });
        },
});
return publicWidget.registry.DeliveryWidget;
});
