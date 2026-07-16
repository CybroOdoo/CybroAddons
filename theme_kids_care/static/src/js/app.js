/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

/**
 * Main application widget for the Kids Care theme.
 * Handles responsive navigation toggling, documentation sidebar active states,
 * and code highlighting initialization.
 */
publicWidget.registry.KidsCareApp = publicWidget.Widget.extend({
  selector: 'body',
  events: {
    'click #toggle-nav': '_onToggleNav',
  },
  /**
   * @override
   */
  start() {
    // responsive nav
    this._navBar = this.$('.nav-bar');
    // pseudo active
    if (document.body.classList.contains('editor_enable')) {
        return this._super(...arguments);
    }
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
    return this._super(...arguments);
  },
  /**
   * Toggles the active state of the navigation bar.
   * @private
   * @param {Event} e
   */
  _onToggleNav(e) {
    e.preventDefault();
    const navBar = this._navBar || this.$('.nav-bar');
    navBar.toggleClass('active');
  },
});

export default publicWidget.registry.KidsCareApp;