/*
    This JavaScript file defines a custom widget for the Classic Store theme.
    The widget adds functionality to show or hide a product sidebar when a arrow is clicked.
*/
odoo.define('theme_classic_store', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    publicWidget.registry.show = publicWidget.Widget.extend({
        selector: '.product_sidebar',
        events: {
            'click .show_div': '_showDiv',
        },
        start: function () {
            this._super.apply(this, arguments);
            this._setupEventDelegation();
        },
        _setupEventDelegation: function () {
            this.$el.on('click', '.fa-angle-down.dropdown-arrow', this._showDiv.bind(this));
        },
        _showDiv: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var arrow = this.$(ev.currentTarget);
            var div = arrow[0].parentElement.parentElement.nextElementSibling;
             if (div.hasAttribute('hidden')) {
        div.removeAttribute('hidden');
    } else {
        div.setAttribute('hidden', '');
    }
        },
    });
    return {
        show: publicWidget.registry.show,
    };
});