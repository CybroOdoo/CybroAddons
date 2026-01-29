/**
 * Custom JavaScript functionality for the Diva theme's homepage (Part 2).
 *
 * This module defines various interactive features and behaviors for the Diva theme's homepage.
 * It initializes multiple Owl Carousels with different configurations for displaying content.
 *
 * @module theme_diva.index2
 */
odoo.define('theme_diva.index2', function(require) {
  "use strict";
  var core = require('web.core');
  var Widget = require('web.Widget');
  var MyCustomWidget = Widget.extend({
    /**
     * Starts the custom widget by initializing multiple Owl Carousels.
     */
    start: function() {
      this._initializeOwlCarousel('#slide-testimonal', {
        margin: 0,
        center: true,
        loop: true,
        nav: false,
        lazyLoad: true,
        smartSpeed: 450,
        autoplay: false,
        autoplaySpeed: 1000,
        autoPlayTimeout: 1000,
        autoplayHoverPause: true,
        dots: true,
        responsiveClass: true,
        responsive: {
          0: {
            items: 1
          },
          768: {
            items: 2,
            margin: 15
          },
          1000: {
            items: 3
          }
        }
      });
      this._initializeOwlCarousel('#owl-theme2', {
        items: 3,
        loop: true,
        margin: 30,
        stagePadding: 0,
        smartSpeed: 450,
        autoplay: false,
        lazyLoad: true,
        autoplaySpeed: 1000,
        autoPlayTimeout: 1000,
        autoplayHoverPause: true,
        dots: false,
        nav: true,
        navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
        responsiveClass: true,
        responsive: {
          0: {
            items: 1
          },
          768: {
            items: 2
          },
          1000: {
            items: 3
          }
        }
      });
      this._initializeOwlCarousel('#owl-theme3', {
        items: 1,
        loop: true,
        margin: 30,
        stagePadding: 0,
        smartSpeed: 450,
        autoplay: false,
        lazyLoad: true,
        autoplaySpeed: 1000,
        autoPlayTimeout: 1000,
        autoplayHoverPause: true,
        dots: true,
        nav: false,
        navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>', '<i class="fa fa-angle-right" aria-hidden="true"></i>']
      });
      this._initializeOwlCarousel('#owl-theme4', {
        items: 5,
        loop: true,
        margin: 30,
        stagePadding: 0,
        smartSpeed: 450,
        autoplay: false,
        lazyLoad: true,
        autoplaySpeed: 1000,
        autoPlayTimeout: 1000,
        autoplayHoverPause: false,
        dots: false,
        nav: false,
        responsiveClass: true,
        responsive: {
          0: {
            items: 2
          },
          768: {
            items: 3
          },
          1000: {
            items: 4
          }
        }
      });
    },
     /**
     * Initializes an Owl Carousel with the given selector and options.
     *
     * @private
     * @param {string} selector - The selector for the target element.
     * @param {Object} options - Configuration options for the Owl Carousel.
     */
    _initializeOwlCarousel: function(selector, options) {
      this.$(selector).owlCarousel(options);
    }
  });
  core.action_registry.add('theme_diva.index2', MyCustomWidget);
});
