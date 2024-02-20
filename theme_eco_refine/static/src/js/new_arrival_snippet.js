odoo.define('theme_eco_refine.new_arrival_products', function(require) {
    "use strict";
    var PublicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
     /**
     * Widget for displaying top-selling products in categories.
     */
    var NewArrivalProducts = PublicWidget.Widget.extend({
        selector: '.product_new_arrival_snippet',
        xmlDependencies: ['/theme_eco_refine/static/src/xml/new_arrival_snippet_templates.xml'],
        /**
         * Render the widget with the fetched data.
         */
        start: function() {
            var self = this;
            var products = this.products
            var categories = this.categories
            const current_website_id = this.website_id
            ajax.jsonRpc('/new_arrivals', 'call', {}).then(function(data) {
            self.$('#new_arrival_carousel').html(data);})
        }
    })
    PublicWidget.registry.product_new_arrival_snippet = NewArrivalProducts;
    return NewArrivalProducts;
})
