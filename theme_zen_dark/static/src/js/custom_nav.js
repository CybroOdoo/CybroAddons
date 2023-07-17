odoo.define('theme_zen_dark.custom_nav', function (require) {
'use strict';
    var publicWidget = require('web.public.widget');
    /*
    * Extended public widget to animate the menu icon.
    */
    publicWidget.registry.customMenuBar = publicWidget.Widget.extend({
        selector: 'header#top',
        events: {
            'show.bs.collapse #top_menu_collapse': 'menuOnClick',
            'hide.bs.collapse #top_menu_collapse': 'menuOnClickHide',
        },
        start: function () {
            if(this.$('section').hasClass('header')){
               this.$('header').css('margin-bottom','0');
            }
            else {
               this.$('header').css('margin-bottom','100px')
            };
        },
        menuOnClick: function () {
           this.$el.find('#menu-bar').addClass('change')
        },
        menuOnClickHide: function () {
           this.$el.find('#menu-bar').removeClass('change')
        },
    });
    /*
    * Extended public widget to change the search icon.
    */
    publicWidget.registry.customProductHeader = publicWidget.Widget.extend({
        selector: '.oe_search_button',
        start: function () {
            this.$el.find('.oi').removeClass('oi-search')
            this.$el.find('.oi').addClass('fa')
            this.$el.find('.oi').addClass('fa-search')
        },
    });
});
