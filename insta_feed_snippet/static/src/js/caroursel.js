odoo.define('insta_feed_snippet.carousel_dashboard', function(require){
    'use strict';
    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    Animation.registry.get_dashbaord_carousel = Animation.Class.extend({
        selector : '.s_carousel_template',
        init: function() {
            this._super.apply(this, arguments);
        },
        start: function(){
            console.log("Test");
            var self = this;
            ajax.jsonRpc('/get_dashbaord_carousel', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});
