/** @odoo-module **/
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
// patch navbar for adding new sidebar functionality
patch(NavBar.prototype, 'backend_theme_odoo12', {
    setup(){
        return this._super(...arguments);
    },
    //toggle sidebar on click
    openSidebar(ev){
        var $el = $(ev.target).parents().find('header #sidebar_panel')
        var action = $(ev.target).parents().find('body .o_action_manager')
        if (!$(ev.target).hasClass('opened')){
            $el.show()
            $(ev.target).toggleClass('opened')
            $el.css({'display':'block'});
            action.css({'margin-left': '320px','transition':'all .1s linear'});
        }
        else{
            $el.hide()
            $(ev.target).toggleClass('opened')
            $el.css({'display':'none'});
            action.css({'margin-left': '0px'});
        }
    },
    clickSidebar(ev){
        var $el = $(ev.target).parents().find('header #sidebar_panel').css({'display':'none'});
        var action = $(ev.target).parents().find('body .o_action_manager').css({'margin-left': '0px'});
    },
});
