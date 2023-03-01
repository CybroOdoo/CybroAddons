odoo.define('theme_silon.most_popular',function(require){
'use strict';

var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');

Animation.registry.popular = Animation.Class.extend({
    selector : '.most-popular',
    start: function () {
        var self = this;
        ajax.jsonRpc('/get_popular_product', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
    })
})