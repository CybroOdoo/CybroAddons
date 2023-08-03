odoo.define('theme_diva.featured_product', function(require){
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core')
    var QWeb = core.qweb


    publicWidget.registry.featured_product = publicWidget.Widget.extend({
        xmlDependencies: ['theme_diva/static/src/xml/index_featured_products.xml'],
        selector : '.featured',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_featured_product', 'call', {})
            .then((data) => {
                  this.$el.html(QWeb.render('diva_index_features',{
                  featured_products1: data.featured_products1,
                  currency_symbol: data.currency_symbol
                  }))
            });
        }
    });
});