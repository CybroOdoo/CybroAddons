odoo.define('theme_diva.featured_product2', function(require){
    'use strict';

     var publicWidget = require('web.public.widget');
     var ajax = require('web.ajax');
     var core = require('web.core')
    var QWeb = core.qweb

    publicWidget.registry.get_featured_products = publicWidget.Widget.extend({
        xmlDependencies: ['theme_diva/static/src/xml/index_featured_products2.xml'],
        selector : '.featured_2',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_featured_products', 'call', {})
            .then((data) => {
                  this.$el.html(QWeb.render('diva_index2_features',{
                  featured_products2: data.featured_products2,
                  currency_symbol: data.currency_symbol
                  }))
            });
        }
    });
});