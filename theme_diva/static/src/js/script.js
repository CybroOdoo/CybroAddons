/**
 * Custom JavaScript functionality for the Diva theme's scripts.
 *
 * This module defines a custom widget that handles various interactive behaviors for the theme,
 * such as fixing the height of the navigation menu, toggling the mobile menu, and managing overlays.
 *
 * @module theme_diva.script
 */
odoo.define('theme_diva.script', function(require) {
  "use strict";
  var core = require('web.core');
  var Widget = require('web.Widget');
  var MyCustomWidget = Widget.extend({
  /**
     * Starts the custom widget by setting up event listeners and initial behaviors.
     */
    start: function() {
      this._fixHeight();
      $(window).resize(this._fixHeight.bind(this));
      this.$('.navbar-toggler').on('click', this._onClickNavbarToggler.bind(this));
      this.$('.navbar-toggler, .overlay').on('click', this._onClickOverlay.bind(this));
    },
    /**
     * Adjusts the maximum height of the navigation menu based on the viewport height.
     *
     * @private
     */
    _fixHeight: function() {
      var navbarNav = this.$('.navbar-nav');
      navbarNav.css('max-height', document.documentElement.clientHeight - 150);
    },
    /**
     * Toggles the mobile menu and overlay when the navbar toggler is clicked.
     *
     * @private
     */
    _onClickNavbarToggler: function() {
      this._fixHeight();
      this.$('.mobileMenu, .overlay').toggleClass('open');
    },
    /**
     * Toggles the mobile menu and overlay when the overlay is clicked.
     *
     * @private
     */
    _onClickOverlay: function() {
      this.$('.mobileMenu, .overlay').toggleClass('open');
    }
  });
  core.action_registry.add('theme_diva.script', MyCustomWidget);
});
