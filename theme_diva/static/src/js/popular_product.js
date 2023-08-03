odoo.define('theme_diva.popular_product', function(require){
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core')

     publicWidget.registry.get_main_product = publicWidget.Widget.extend({
        xmlDependencies: ['theme_diva/static/src/xml/index_main_product.xml'],
        selector : '.main_product',
        start: function(){
            var self = this;
            var QWeb = core.qweb
            ajax.jsonRpc('/get_main_product', 'call', {})
            .then((data) => {
                  this.$el.empty().append(QWeb.render('diva_index_main_product',{
                  main_products: data.main_products,
                  }))
            });
        }
    });
});