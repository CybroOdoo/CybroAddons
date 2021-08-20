odoo.define('theme_diva.popular_product', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

//    Animation.registry.get_popular_product = Animation.Class.extend({
//        selector : '.populor',
//        start: function(){
//            var self = this;
//            ajax.jsonRpc('/get_popular_product', 'call', {})
//            .then(function (data) {
//                if(data){
//                    self.$target.empty().append(data);
//                }
//            });
//        }
//    });
     Animation.registry.get_main_product = Animation.Class.extend({
        selector : '.main_product',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_main_product', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});