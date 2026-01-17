/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.customMenuBar = publicWidget.Widget.extend({
    selector: 'header#top',
    events: {
        'show.bs.collapse #top_menu_collapse': 'menuOnClick',
        'hide.bs.collapse #top_menu_collapse': 'menuOnClickHide',
    },
    start: function () {
        if(this.$el.find('section').hasClass('header')){
           this.$el.find('header').css('margin-bottom','0');
        }
        else {
           this.$el.find('header').css('margin-bottom','100px')
        };
    },
    menuOnClick: function () {
       this.$el.find('#menu-bar').addClass('change');
    },
    menuOnClickHide: function () {
       this.$el.find('#menu-bar').removeClass('change');
    },
});