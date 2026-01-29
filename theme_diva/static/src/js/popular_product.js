/**
 * Custom JavaScript functionality for displaying popular products on the Diva theme's homepage.
 *
 * This module defines a public widget that fetches and displays popular products using AJAX requests.
 * It renders the main product section on the homepage with the provided data.
 *
 * @module theme_diva.popular_product
 */
odoo.define('theme_diva.popular_product', function(require){
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb
    /**
     * Public widget to display popular products on the homepage.
     */
    publicWidget.registry.get_main_product = publicWidget.Widget.extend({
        xmlDependencies: ['/theme_diva/static/src/xml/index_main_product.xml', '/theme_diva/static/src/xml/index_main_product_templates.xml'],
        selector : '.main_product1',
        start: function(){
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/get_main_product', 'call', {})
            .then((data) => {
                  this.$el.empty().append(QWeb.render('diva_index_main_product1',{
                  main_products: data.main_products,
                  }));
            });
        }
    });
});
