odoo.define('theme_fashion.custom', function (require) {
"use strict"
var publicWidget = require('web.public.widget');
publicWidget.registry.Main_nav = publicWidget.Widget.extend({
   selector: '.main-nav',
   events: {
        'click #openbtn': 'openNav',
        'click #closebtn': 'closeNav',
    },

   /* Set the width of the sidebar to 250px and the left margin of the page content to 250px */
    openNav: function () {
         var self = this;
         self.$el.find("#mySidebar").width("250px");
        },

   /* Set the width of the sidebar to 0 and the left margin of the page content to 0 */
     closeNav: function () {
         var self = this;
         self.$el.find("#mySidebar").width("0");
        },
});

return publicWidget.registry.Main_nav;
});
