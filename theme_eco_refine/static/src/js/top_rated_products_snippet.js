odoo.define('theme_eco_refine.rated_products', function(require) {
    "use strict";
    var PublicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
     /**
     * Widget for displaying top-selling products in categories.
     */
    var RatedProducts = PublicWidget.Widget.extend({
        selector: '.top_rated_product_snippet',
        xmlDependencies: ['/theme_eco_refine/static/src/xml/top_rated_product_snippet_templates.xml'],
        /**
         * Render the widget with the fetched data.
         */
        start: function() {
            var self = this;
            var products = this.products
            var categories = this.categories
            const current_website_id = this.website_id
            ajax.jsonRpc('/top_rated', 'call', {}).then(function(data) {
            self.$('#top_rated_carousel').html(data);})
        }
    })
    PublicWidget.registry.top_rated_product_snippet = RatedProducts;
    return RatedProducts;
})
