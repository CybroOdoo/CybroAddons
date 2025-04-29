/** @odoo-module **/
    import publicWidget from "@web/legacy/js/public/public_widget";
    publicWidget.registry.PropertyItemView = publicWidget.Widget.extend({
    selector: '.property_item_container',
    events: {
            'click #loadMap': 'MapLoad',
    },
    /** Loads the map location of the property **/
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
