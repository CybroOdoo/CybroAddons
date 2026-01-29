odoo.define('theme_eco_refine.top_selling_products', function(require) {
    "use strict";
    var PublicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    /**
     * Widget for displaying top-selling products in categories.
     */
    var TopSellingProducts = PublicWidget.Widget.extend({
        selector: '.best_seller_product_snippet',
        xmlDependencies: ['/theme_eco_refine/static/src/xml/best_seller_snippet_templates.xml'],
        /**
         * Render the widget with the fetched data.
         */

        start: function() {
            var self = this;
            var products = this.products
            var categories = this.categories
            const current_website_id = this.website_id
            ajax.jsonRpc('/bestsellers', 'call', {}).then(function(data) {
            self.$('#top_products_carousel').html(data);})
        }
    })
    PublicWidget.registry.products_category_wise_snippet = TopSellingProducts;
    return TopSellingProducts;
})
