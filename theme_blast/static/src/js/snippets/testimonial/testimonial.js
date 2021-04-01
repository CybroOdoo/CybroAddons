odoo.define('theme_blast.testimonial',function(require){
'use strict';

var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');

Animation.registry.testimonial = Animation.Class.extend({
    selector : '.testiomnial',
    start: function () {
        var self = this;
        ajax.jsonRpc('/get_testimonial', 'call', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
                self.testimonial_slider();
            }
        });

    },

    testimonial_slider: function (autoplay=false, items=1, slider_timing=5000) {
        var self= this;
         $("#testi").owlCarousel(
        {
          // animateOut: 'slideOutDown',
          // animateIn: 'flipInX',
          items: 1,
          loop: true,
          margin: 40,
          stagePadding: 30,
          smartSpeed: 450,
          autoplay: true,
          autoPlaySpeed: 1000,
          autoPlayTimeout: 1000,
          autoplayHoverPause: true,
          onInitialized: counter,
          dots: true,
          nav: true,
          navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
//           responsiveClass: true,
//           responsive: {
//             0: {
//               items: 1,
//               nav: true
//             },
//             600: {
//               items: 2,
//               nav: true,
//             },
//             1000: {
//               items: 4,
//               nav: true,
//               loop: true,
//             }
//           }
        }
      );
    function counter() {
      var buttons = $('.owl-dots button');
      buttons.each(function (index, item) {
        // $(item).find('span').text(index + 1);
      });
    };
    }
    })
    })
