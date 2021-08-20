odoo.define('theme_diva.blog', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    Animation.registry.get_blog_post = Animation.Class.extend({
        selector : '.blog_index',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_blog_post', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });

    Animation.registry.get_blog_posts = Animation.Class.extend({
        selector : '.blog_2',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_blog_posts', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});