odoo.define('advanced_property_management.property_item', function (require) {
'use strict';
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');

    publicWidget.registry.PropertyItemView = publicWidget.Widget.extend({
    templates: 'advanced_property_management.property_view_item',
    selector: '.property_container',
    events: {
            'click #loadMap': 'MapLoad',
    },
    //Loads the map location of the property
    MapLoad: function (e) {
            this.$('#map-view').css('display', 'block')
            this.$('#loadMap').css('display', 'none')
            var lat = parseFloat(e.target.dataset.lat)
            var lng = parseFloat(e.target.dataset.lng)
            const location = { lat: lat, lng: lng };
            const map = new google.maps.Map(document.getElementById("map-view"),
            {
            zoom: 12,
            center: location,

            });
            const marker = new google.maps.Marker({
            position: location,
            map: map,
            });
    },
    });
    return publicWidget.registry.PropertyItemView ;
})
