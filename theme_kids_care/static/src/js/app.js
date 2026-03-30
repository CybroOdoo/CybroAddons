/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.KidsCareApp = publicWidget.Widget.extend({
  selector: 'body',
  events: {
    'click #toggle-nav': '_onToggleNav',
  },
  start() {
    // responsive nav
    this._navBar = this.$('.nav-bar');

    // pseudo active
    if (this.$('#docs').length) {
      const sidenav = this.$('ul.side-nav').find('a');
      const parts = window.location.pathname.split('/');
      const url = parts[parts.length - 1];

      sidenav.each(function (i, e) {
        const active = $(e).attr('href');

        if (active === url) {
          $(e).parent('li').addClass('active');
          return false;
        }
      });
    }

    // highlight.js
    if (typeof window.hljs !== 'undefined') {
      window.hljs.configure({ tabReplace: '  ' });
      window.hljs.initHighlightingOnLoad();
    }

    // Initialize Owl Carousel for "All the Sneakers" section
    // Only initialize if the Owl Carousel jQuery plugin is present
    if (typeof window.$ !== 'undefined' && $.fn && $.fn.owlCarousel) {
      $('.owl-carousel').owlCarousel({
        loop: true,
        margin: 10,
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
            items: 2,
            nav: true,
            loop: false,
            margin: 20
          }
        }
      });

      // Initialize second carousel if exists
      $('.second-carousel').owlCarousel({
        loop: true,
        margin: 10,
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
            items: 2,
            nav: true,
            loop: false,
            margin: 20
          }
        }
      });

      // Initialize third carousel if exists
      $('.thred-carousel').owlCarousel({
        loop: true,
        margin: 10,
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
            items: 5,
            nav: true,
            loop: false,
            margin: 20
          }
        }
      });
    }

    return this._super(...arguments);
  },

  _onToggleNav(e) {
    e.preventDefault();
    const navBar = this._navBar || this.$('.nav-bar');
    navBar.toggleClass('active');
  },
});

export default publicWidget.registry.KidsCareApp;