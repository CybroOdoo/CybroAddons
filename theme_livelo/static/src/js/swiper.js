/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.Swiper = publicWidget.Widget.extend({
  selector: '.swiper',
  start: function () {
    // Disable Swiper in Edit Mode to avoid conflicts with Odoo Website Builder
    if (this.editableMode) {
      return;
    }
    // Ensure Swiper is available before initializing
    if (typeof Swiper === 'undefined') {
      console.error('Swiper is not loaded');
      return;
    }
    // SAFEGUARD: Only initialize if this is a real swiper with a wrapper inside!
    if (!this.el.querySelector('.swiper-wrapper')) {
      return;
    }
    var paginationEl = this.el.querySelector('.swiper-pagination') || (this.el.parentNode && this.el.parentNode.querySelector('.swiper-pagination'));
    var options = {
      slidesPerView: 3,
      spaceBetween: 20,
      breakpoints: {
        320: {
          slidesPerView: 1,
          spaceBetween: 20
        },
        480: {
          slidesPerView: 1,
          spaceBetween: 30
        },
        640: {
          slidesPerView: 2,
          spaceBetween: 40
        },
        991: {
          slidesPerView: 3,
          spaceBetween: 40
        }
      }
    };
    if (paginationEl) {
      options.pagination = {
        el: paginationEl,
        clickable: true
      };
    }
    var swiper = new Swiper(this.el, options);
  },
});