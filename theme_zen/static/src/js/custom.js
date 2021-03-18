// $(document).ready(function () {
//      $("#banner").owlCarousel(
//        {
//
//
//          items: 1,
//          autoHeight: true,
//          loop: true,
//          margin: 0,
//          stagePadding: 0,
//          smartSpeed: 450,
//          autoplay: false,
//          autoPlaySpeed: 1000,
//          autoPlayTimeout: 5000,
//          autoplayHoverPause: true,
//          onInitialized: counter,
//          dots: true,
//          nav: true,
//          navText: ['<i class="material-icons" aria-hidden="true">keyboard_arrow_left</i>', '<i class="material-icons" aria-hidden="true">navigate_next</i>'],
//          responsiveClass: true,
//          // responsive:{
//          //     0:{
//          //         items:1,
//          //         nav:true
//          //     },
//          //     600:{
//          //         items:1,
//          //         nav:false
//          //     },
//          //     1000:{
//          //         items:1,
//          //         nav:true,
//          //         loop:false
//          //     }
//          // }
//        }
//      );
//      $("#owl-theme2").owlCarousel(
//        {
//          items: 1,
//          loop: true,
//          margin: 10,
//          stagePadding: 10,
//          smartSpeed: 450,
//          autoplay: false,
//          autoPlaySpeed: 1000,
//          autoPlayTimeout: 1000,
//          autoplayHoverPause: true,
//          dots: true,
//          nav: false,
//          navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>', '<i class="fa fa-angle-right" aria-hidden="true"></i>'],
//
//
//        }
//      );
//    });
//    function counter() {
//      var buttons = $('.owl-dots button');
//      buttons.each(function (index, item,) {
//        $(item).find('span').text(index + 1);
//      });
//    }

odoo.define('theme_blasst.best_products_carousel',function(require){
'use strict';

var sAnimation = require('website.content.snippets.animation');
var ajax = require('web.ajax');


sAnimation.registry.banner_snippet = sAnimation.Class.extend({
    selector : '.banner_snippet',
    disabledInEditableMode: false,
    start: function () {
        var self = this;
        self.initialize_owl();
    },

    initialize_owl: function (autoplay=false, items=4, slider_timing=5000) {
        var self= this;
        $("#banner").owlCarousel(
        {
          items: 1,
          autoHeight: true,
          loop: true,
          margin: 0,
          stagePadding: 0,
          smartSpeed: 450,
          autoplay: true,
          autoPlaySpeed: 1000,
          autoPlayTimeout: 5000,
          autoplayHoverPause: true,
//          onInitialized: this.counter,
          dots: true,
          nav: true,
          navText: ['<i class="material-icons" aria-hidden="true">keyboard_arrow_left</i>', '<i class="material-icons" aria-hidden="true">navigate_next</i>'],
          responsiveClass: true,
          // responsive:{
          //     0:{
          //         items:1,
          //         nav:true
          //     },
          //     600:{
          //         items:1,
          //         nav:false
          //     },
          //     1000:{
          //         items:1,
          //         nav:true,
          //         loop:false
          //     }
          // }
        }
      );
    },

    counter:  function() {
      var buttons = $('.owl-dots button');
      buttons.each(function (index, item,) {
//        $(item).find('span').text(index + 1);
      });
    }
});

sAnimation.registry.testimonial_main = sAnimation.Class.extend({
    selector : '.testimonial_main',
    start: function () {
        var self = this;
        self.initialize_owl();
    },

    initialize_owl: function (autoplay=false, items=4, slider_timing=5000) {
        var self= this;
        $("#owl-theme2").owlCarousel(
        {
          items: 1,
          loop: true,
          margin: 10,
          stagePadding: 10,
          smartSpeed: 450,
          autoplay: false,
          autoPlaySpeed: 1000,
          autoPlayTimeout: 1000,
          autoplayHoverPause: true,
          dots: true,
          nav: false,
          navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>', '<i class="fa fa-angle-right" aria-hidden="true"></i>'],
        }
      );
    },

    counter:  function() {
      var buttons = $('.owl-dots button');
      buttons.each(function (index, item,) {
        $(item).find('span').text(index + 1);
      });
    }
});

});
