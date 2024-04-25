odoo.define('theme_diva.featured_product2', function(require){
    'use strict';
     var publicWidget = require('web.public.widget');
     var ajax = require('web.ajax');
     var core = require('web.core')
    var QWeb = core.qweb
    publicWidget.registry.get_featured_products = publicWidget.Widget.extend({
    /*
        Widget for displaying more featured products on a webpage.
        Attributes:
            xmlDependencies (Array[str]): List of XML dependencies for this widget.
            selector (str): CSS selector for the widget's target element.
        */
        xmlDependencies: ['/theme_diva/static/src/xml/index_featured_products2_templates.xml'],
        selector : '.featured_2',
        start: function(){
         /*
            Function called when the widget starts.
            Retrieves more featured product data and renders the template.
            */
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
