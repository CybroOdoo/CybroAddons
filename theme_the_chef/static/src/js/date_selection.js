odoo.define('theme_the_chef.date_selection', function (require) {
"use strict"
//    Date Selection
    var PublicWidget = require('web.public.widget');
    var DateSelection = PublicWidget.Widget.extend({
       selector: '.booking',
       start: function() {
            var self = this;
            this._onClick();
       },
        _onClick: function () {
             var self = this;
            if(self.$el.find('#date-picker').length){
            this.$el.find('#date-picker')[0].min = new Date().toISOString().split("T")[0];
            }
        },
    });
   PublicWidget.registry.booking = DateSelection;
   return DateSelection;
});