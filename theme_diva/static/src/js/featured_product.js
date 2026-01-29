odoo.define('theme_diva.featured_product', function(require){
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core')
    var QWeb = core.qweb
    publicWidget.registry.featured_product = publicWidget.Widget.extend({
     /*
        Widget for displaying featured products on a webpage.
        Attributes:
            xmlDependencies (Array[str]): List of XML dependencies for this widget.
            selector (str): CSS selector for the widget's target element.
        */
        xmlDependencies: ['/theme_diva/static/src/xml/index_featured_products_templates.xml'],
        selector : '.featured',
        start: function(){
         /*
            Function called when the widget starts.
            Retrieves featured product data and renders the template.
            */
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
