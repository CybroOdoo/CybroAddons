/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.Scroll = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click #back-to-top': '_OnClick',
    },
    _OnClick(){
         $('body,html').animate({
             scrollTop: 0
         }, 400);
         return false;
    }
})
