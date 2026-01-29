/**
 * Custom JavaScript functionality for the Diva theme's homepage (Part 3).
 *
 * This module defines various interactive features and behaviors for the Diva theme's homepage.
 * It includes functions for initializing a slider with Owl Carousel, creating image hover effects,
 * and applying animations using AOS library.
 *
 * @module theme_diva.index3
 */
odoo.define('theme_diva.index3', function(require) {
  "use strict";
  var core = require('web.core');
  var Widget = require('web.Widget');
  var MyCustomWidget = Widget.extend({
  /**
     * Starts the custom widget by initializing slider, image hover effect, and AOS animations.
     */
    start: function() {
      this._initializeSlider();
      this._initializeImageHoverEffect();
      this._initializeAOS();
    },
    /**
     * Initializes the slider using Owl Carousel.
     *
     * @private
     */
    _initializeSlider: function() {
      $("#slider2").owlCarousel({
        items: 3,
        loop: true,
        smartSpeed: 450,
        autoplay: true,
        autoplaySpeed: 1000,
        autoPlayTimeout: 1000,
        autoplayHoverPause: true,
        dots: true,
        nav: true,
        navText: [
          '<i class="bi bi-arrow-left-short"></i>    <span class="bi bi-arrow-left-circle"></span>',
          '<i class="bi bi-arrow-right-short"></i> <i class="bi bi-arrow-right-circle"></i>'
        ],
        animateOut: 'fadeOut',
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
            loop: false
          }
        }
      });
    },
    /**
     * Initializes the image hover effect.
     *
     * @private
     */
    _initializeImageHoverEffect: function() {
      var self = this;
      this.$('.sustainable_wrapper').on({
        mouseover: function() {
          $(this).find("img:nth-child(1)").stop().animate({ opacity: 0 }, 600);
          $(this).find("img:nth-child(2)").stop().animate({ opacity: 1 }, 600);
        },
        mouseout: function() {
          $(this).find("img:nth-child(1)").stop().animate({ opacity: 1 }, 600);
          $(this).find("img:nth-child(2)").stop().animate({ opacity: 0 }, 600);
        }
      });
    },
     /**
     * Initializes AOS animations.
     *
     * @private
     */
    _initializeAOS: function() {
      AOS.init({
        easing: 'ease-in-quad'
      });
    }
  });
  core.action_registry.add('theme_diva.index3', MyCustomWidget);
});
