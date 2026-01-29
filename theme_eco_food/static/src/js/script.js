/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MyNavbar = publicWidget.Widget.extend({
    selector: '.navbar',
    start: function () {
        this._super(...arguments);
        this._fixHeight();
        $(window).on('resize', this._fixHeight.bind(this));
        this.$('.navbar-toggler').on('click', this._fixHeight.bind(this));
        this.$('.navbar-toggler, .overlay').on('click', this._toggleMobileMenu.bind(this));
    },
    _fixHeight: function () {
        this.$('.navbar-nav').css('max-height', document.documentElement.clientHeight);
    },
    _toggleMobileMenu: function () {
        this.$('.mobileMenu, .overlay').toggleClass('open');
    },
});