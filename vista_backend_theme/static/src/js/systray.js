/* @odoo-module */
import { Component,useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";

//Create a Component Themewidget Adding to Systray
export class ThemeWidget extends Component{
    static template="vista_backend_theme.theme_systray"
    setup(){ //Create setup function add states and Actions
        this.state=useState({
            is_admin:false,
        })
        this.action = useService("action");
        console.log(session.storeData['res.partner'])
        console.log(session.storeData.Store.self.id)
//        console.log(session.storeData['res.partner'].filter((partner)=>partner.userId === session.user_id[0]))
        var admin = session.storeData['res.partner'].find((partner)=>partner.id == session.storeData.Store.self.id)
        console.log(admin)
        this.state.is_admin=admin.isAdmin;
    }
    _onClick(){ // create a onclick function for click on brush icon open the theme data wizard
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'theme data',
            res_model: 'theme.data',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new'
        })
    }
}
registry.category("systray").add("vista_backend_theme.theme_widget",{Component:ThemeWidget}, { sequence:20})
