odoo.define('theme_diva.featured_product2', function(require){
    'use strict';

     var Animation = require('website.content.snippets.animation');
     var ajax = require('web.ajax');

    Animation.registry.get_featured_products = Animation.Class.extend({
        selector : '.featured_2',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_featured_products', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});