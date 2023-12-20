odoo.define('theme_autofly.dynamic_blog_snippet', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    Animation.registry.blog_snippet = Animation.Class.extend({
        selector : '.blog_index',
        start: function(){
            var self = this;
            ajax.jsonRpc('/dynamic_blog', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});