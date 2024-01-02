/** @odoo-module **/
//    Date Selection
import publicWidget from "@web/legacy/js/public/public_widget";
    var DateSelection = publicWidget.Widget.extend({
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
   publicWidget.registry.booking = DateSelection;
   return DateSelection;
