odoo.define('theme_classic_store.trending', function(require){
'use strict';
var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');
/**
 * Defines an animation class for the trending element in the HTML document.
 * Sends an AJAX request to the /classic_product_trending URL using the ajax.jsonRpc
 * method, and calls the 'call' method on the server-side. If the request is successful,
 * clears the current content of the trending element using the empty method on the
 * self.$target jQuery object, and appends the returned data to the element using the
 * append method. Initializes the owl carousel on the .owl-carousel element inside the
 * trending element with the specified options. The selector property defines the CSS
 * selector for the element that the animation will be applied to.
 *
 * @module theme_classic_store.price_filter
 * @extends Animation.Class
 */
Animation.registry.trending = Animation.Class.extend({
    selector : '.trending',
    start: function(){
        var self = this;
        ajax.jsonRpc('/classic_product_trending', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
                self.product_carousel();
            }
        });
    },
    product_carousel: function (autoplay=false, items=4, slider_timing=5000) {
        var self= this;
            this.$el.find(".owl-carousel").owlCarousel(
                {
                    items: 3,
                    loop: true,
                    margin: 30,
                    stagePadding: 30,
                    smartSpeed: 450,
                    autoplay: true,
                    autoPlaySpeed: 1000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    onInitialized: self.counter(),
                    dots: true,
                    nav: true,
                    responsiveClass: true,
                    responsive: {
                        0: {
                            items: 1,
                            nav: true
                        },
                        600: {
                            items: 2,
                            nav: false
                        },
                        1000: {
                            items: 3,
                            nav: true,
                            loop: true
                        }
                    }
                }
            );
        },
        counter:  function() {
            var buttons = this.$el.find('.owl-dots button');
            buttons.each(function (index, item) {
                $(item).find('span').text(index + 1);
            });
        }
});
});