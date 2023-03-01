odoo.define('theme_silon.trending',function(require){
'use strict';

var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');

Animation.registry.trending_product = Animation.Class.extend({
    selector : '.trending',
    start: function () {
        var self = this;
        ajax.jsonRpc('/get_trending_product', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
    })
})