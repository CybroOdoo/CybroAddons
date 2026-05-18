/** @odoo-module **/

import animations from "@website/js/content/snippets.animation";
import { rpc } from "@web/core/network/rpc";

animations.registry.voltro_brands_carousel = animations.Class.extend({
  selector: '.brands',
  disabledInEditableMode: false,

  onBuilt: function () {
    this.start();
  },
  onClone: function () {
    this.start();
  },
  start: function () {
    var self = this;
    var $carousel = this.$target.find('#brands');
    if (!$carousel.length) {
        $carousel = this.$('.owl-carousel');
    }
    if ($carousel.length) {
      // Ensure visibility even if owlCarousel fails
      $carousel.css({
          'display': 'block',
          'opacity': '1',
          'visibility': 'visible'
      });
      if (typeof $carousel.owlCarousel === 'function') {
        $carousel.owlCarousel({
          items: 4,
          loop: true,
          margin: 20,
          autoplay: true,
          autoplayTimeout: 3000,
          autoplayHoverPause: true,
          dots: false,
          nav: false,
          responsive: {
            0: { items: 1 },
            600: { items: 2 },
            1000: { items: 4 }
          }
        });
      }
    }
  },
});