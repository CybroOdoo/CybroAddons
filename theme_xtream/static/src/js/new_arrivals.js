odoo.define('theme_xtream.new_arrivals', function(require){
'use strict';

var Animation = require('website.content.snippets.animation');

var ajax = require('web.ajax');

Animation.registry.arrival_product = Animation.Class.extend({
    selector : '.arrivals',
    start: function(){
        var self = this;
        ajax.jsonRpc('/get_arrival_product', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
    });
});