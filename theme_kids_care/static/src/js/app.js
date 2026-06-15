/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.KidsCareApp = publicWidget.Widget.extend({
  selector: 'body',
  events: {
    'click #toggle-nav': '_onToggleNav',
    'click .section-tab .nav-link': '_onShowcaseTabClick',
    'click .section-tab .sizes > div': '_onShowcaseSizeClick',
    'change .section-tab .kids-care-size input[type="radio"]': '_onShowcaseColorChange',
    'click .section-tab .t-shirt-img a': '_onShowcaseThumbnailClick',
  },
  /**
   * @override
   */
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
      $('.owl-carousel').not('.second-carousel, .thred-carousel').owlCarousel({
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
        loop: false,
        margin: 20,
        responsiveClass: true,
        nav: false,
        dots: true,
        responsive: {
          0: {
            items: 1,
            nav: false
          },
          600: {
            items: 2,
            nav: false
          },
          900: {
            items: 3,
            nav: false,
            loop: false,
            margin: 20
          },
          1000: {
            items: 4,
            nav: false,
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
    this._initializeShowcaseSelections();
    return this._super(...arguments);
  },
  /**
   * Toggles the visibility of the mobile navigation bar.
   * @param {Event} e
   */
  _onToggleNav(e) {
    e.preventDefault();
    const navBar = this._navBar || this.$('.nav-bar');
    navBar.toggleClass('active');
  },
  /**
   * Handles tab clicks in the showcase section to switch content panes.
   * @param {Event} e
   */
  _onShowcaseTabClick(e) {
    const link = e.currentTarget;
    const href = link.getAttribute('href');
    if (!href || !href.startsWith('#')) {
      return;
    }
    e.preventDefault();
    const section = link.closest('.section-tab');
    if (!section) {
      return;
    }
    const navLinks = section.querySelectorAll('.nav-link');
    const panes = section.querySelectorAll('.tab-content-babycare > .tab-pane');
    navLinks.forEach((item) => {
      item.classList.remove('active');
      item.setAttribute('aria-selected', 'false');
    });
    panes.forEach((pane) => pane.classList.remove('active', 'show'));
    const targetPane = section.querySelector(href);
    link.classList.add('active');
    link.setAttribute('aria-selected', 'true');
    if (targetPane) {
      targetPane.classList.add('active', 'show');
    }
  },
  /**
   * Handles size selection clicks in the showcase section.
   * @param {Event} e
   */
  _onShowcaseSizeClick(e) {
    const size = e.currentTarget;
    const wrapper = size.closest('.sizes');
    if (!wrapper) {
      return;
    }
    wrapper.querySelectorAll('div').forEach((item) => item.classList.remove('active1'));
    size.classList.add('active1');
  },
  /**
   * Handles color radio button changes in the showcase section.
   * @param {Event} e
   */
  _onShowcaseColorChange(e) {
    const input = e.currentTarget;
    const groupName = input.getAttribute('name');
    if (!groupName) {
      return;
    }
    document.querySelectorAll(`.section-tab input[type="radio"][name="${groupName}"]`).forEach((item) => {
      item.classList.remove('is-selected');
    });
    input.classList.add('is-selected');
  },
  /**
   * Updates the main product image when a thumbnail is clicked.
   * @param {Event} e
   */
  _onShowcaseThumbnailClick(e) {
    e.preventDefault();
    const link = e.currentTarget;
    const pane = link.closest('.tab-pane');
    const image = link.querySelector('img');
    if (!pane || !image) {
      return;
    }
    const mainImage = pane.querySelector('.baby-care-cart-section img');
    if (mainImage) {
      mainImage.setAttribute('src', image.getAttribute('src'));
    }
    pane.querySelectorAll('.t-shirt-img').forEach((item) => item.classList.remove('is-active'));
    const thumb = link.closest('.t-shirt-img');
    if (thumb) {
      thumb.classList.add('is-active');
    }
  },
  /**
   * Initializes default selections for thumbnails and color options in the showcase.
   */
  _initializeShowcaseSelections() {
    this.el.querySelectorAll('.section-tab .tab-pane').forEach((pane) => {
      const firstThumb = pane.querySelector('.t-shirt-img');
      if (firstThumb && !pane.querySelector('.t-shirt-img.is-active')) {
        firstThumb.classList.add('is-active');
      }
      const radioGroup = pane.querySelectorAll('.kids-care-size input[type="radio"]');
      const checkedRadio = pane.querySelector('.kids-care-size input[type="radio"]:checked');
      if (!checkedRadio && radioGroup.length) {
        radioGroup[0].checked = true;
        radioGroup[0].classList.add('is-selected');
      } else if (checkedRadio) {
        checkedRadio.classList.add('is-selected');
      }
    });
  },
});

export default publicWidget.registry.KidsCareApp;
