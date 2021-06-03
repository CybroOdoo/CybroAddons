odoo.define('theme_classic_store.categories', function(require){
'use strict';
var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');

Animation.registry.categories = Animation.Class.extend({
    selector : '.categories',
    start: function(){
        var self = this;
        ajax.jsonRpc('/classic_product_category', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
    });
});