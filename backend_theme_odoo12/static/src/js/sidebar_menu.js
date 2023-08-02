/** @odoo-module **/
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import Widget from 'web.Widget';
import { registry } from "@web/core/registry";
const userMenuRegistry = registry.category("user_menuitems");
// patch navbar for adding new sidebar functionality
patch(NavBar.prototype, 'backend_theme_odoo12', {
    setup(){
        return this._super(...arguments);
    },
    //toggle sidebar on click
    openSidebar(ev){
        let el = document.querySelector('#sidebar_panel')
        let actionManager = document.querySelector('.o_action_manager')

        if (! ev.target.classList.contains('opened')){
            el.style.display = 'block';
            ev.target.classList.toggle('opened');
            actionManager.style.marginLeft = '320px';
            actionManager.style.transition = 'all .1s linear';
        }
        else {
            el.style.display = 'none';
            ev.target.classList.toggle('opened');
            actionManager.style.marginLeft = '0px';
        }
    },
    clickSidebar(ev){
        let el = document.querySelector('#sidebar_panel')
        let actionManager = document.querySelector('.o_action_manager')
        el.style.display = 'none'
        actionManager.style.marginLeft = '0px';
    }
});
