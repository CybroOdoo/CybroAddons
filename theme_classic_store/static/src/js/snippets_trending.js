odoo.define('theme_classic_store.trending', function(require){
'use strict';
var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');

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
            $(".owl-carousel").owlCarousel(
                {
                    // animateOut: 'slideOutDown',
                    // animateIn: 'flipInX',
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
            var buttons = $('.owl-dots button');
            buttons.each(function (index, item) {
                $(item).find('span').text(index + 1);
            });
        }
});
});
