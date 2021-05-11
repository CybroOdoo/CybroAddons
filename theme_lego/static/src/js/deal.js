odoo.define('theme_lego.deal_week', function(require){
'use strict';

var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');

Animation.registry.deal_of_the_week = Animation.Class.extend({
    selector : '.deal',
    start: function(){
        var self = this;
        ajax.jsonRpc('/get_deal_of_the_week', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
    });
});
