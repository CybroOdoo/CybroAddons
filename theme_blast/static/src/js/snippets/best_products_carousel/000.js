odoo.define('theme_blast.best_products_carousel',function(require){
'use strict';

var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');


Animation.registry.best_products_carousel = Animation.Class.extend({
    selector : '.best_products_carousel',
    start: function () {
        var self = this;
        ajax.jsonRpc('/get_product_snippet', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
                self.product_carousel();
            }
        });

    },

    product_carousel: function (autoplay=false, items=4, slider_timing=5000) {
        var self= this;
        $("#product").owlCarousel(
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
//          onInitialized: self.counter(),
          dots: true,
          nav: true,
          navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
          responsiveClass: true,
          responsive: {
            0: {
              items: 1,
              nav: true
            },
            600: {
              items: 2,
              nav: true,
            },
            1000: {
              items: 4,
              nav: true,
              loop: true,
            }
          }
        }
      );
    },

    counter:  function() {
      var buttons = $('.owl-dots button');
      buttons.each(function (index, item) {
        // $(item).find('span').text(index + 1);
      });
    }
});
});
