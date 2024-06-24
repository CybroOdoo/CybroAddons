/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.myNavbar = publicWidget.Widget.extend({
    selector: '.navbar',
    start() {
        this._super(...arguments);
        this._fixHeight();
        $(window).on('resize', this._fixHeight.bind(this));
        this.$('.navbar-toggler').on('click', this._fixHeight.bind(this));
        this.$('.navbar-toggler, .overlay').on('click', this._toggleMobileMenu.bind(this));
        this.$('#pricelistDropdown').on('change', this._handlePricelistChange.bind(this));
    },
    _fixHeight() {
        this.$('.navbar-nav').css('max-height', document.documentElement.clientHeight);
    },
    _toggleMobileMenu() {
        this.$('.mobileMenu, .overlay').toggleClass('open');
    },
    _handlePricelistChange() {
        var selectedPricelistId = this.$('#pricelistDropdown').val();
        window.location.href = '/shop/change_pricelist/' + selectedPricelistId;
    },
});