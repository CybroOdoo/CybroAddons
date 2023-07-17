odoo.define('theme_classic_store.categories', function(require){
'use strict';
    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    /**
     * Defines an animation class for the categories element in the HTML document.
     * Sends an AJAX request to the /classic_product_category URL using the ajax.jsonRpc
     * method, and calls the 'call' method on the server-side. If the request is successful,
     * clears the current content of the categories element using the empty method on the
     * self.$target jQuery object, and appends the returned data to the element using the
     * append method. The selector property defines the CSS selector for the element that
     * the animation will be applied to.
     *
     * @module theme_classic_store.price_filter
     * @extends Animation.Class
     */
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