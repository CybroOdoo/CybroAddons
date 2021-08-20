odoo.define('theme_diva.featured_product', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    Animation.registry.get_featured_product = Animation.Class.extend({
        selector : '.featured',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_featured_product', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});