odoo.define('theme_boec.product_tab', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    Animation.registry.get_product_tab = Animation.Class.extend({
        selector : '.product_tab_class',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_product_tab', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});