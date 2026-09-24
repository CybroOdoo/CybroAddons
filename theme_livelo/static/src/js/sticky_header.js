/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.StickyHeader = publicWidget.Widget.extend({
    selector: 'header.header-shadow',
    start: function () {
        this._onScroll = this._onScroll.bind(this);
        window.addEventListener('scroll', this._onScroll);
        // Initial call to check scroll position on load
        this._onScroll();
        return this._super.apply(this, arguments);
    },
    destroy: function () {
        window.removeEventListener('scroll', this._onScroll);
        this._super.apply(this, arguments);
    },
    _onScroll: function () {
        if (window.scrollY > 50) {
            this.el.classList.add('header-scrolled');
        } else {
            this.el.classList.remove('header-scrolled');
        }
    }
});
