/** @odoo-module **/

const { Component, hooks} = owl;
const { useState } = hooks;
import { useService } from "@web/core/utils/hooks";

export class AppItem extends Component{
    setup(){
        this.menuService = useService('menu');
        this.state= useState({
            active:false
        })
    }
    mounted() {
        this.env.bus.on("MENUS:APP-CHANGED", this, this.on_app_changed);
    }

    willUnmount() {
        this.env.bus.off("MENUS:APP-CHANGED", this);
    }
    on_app_changed() {

        var current_app = this.menuService.getCurrentApp();
        var first_app = current_app;
        while (first_app.parent) {
            first_app = first_app.parent;
            first_app.open = true
        }

        if (first_app.id == this.app.id) {
            this.state.active = true;
        } else {
            this.state.active = false;
        }
    }
    getMenuItemHref() {
        const parts = [`menu_id=${this.app.id}`];
        if (this.app.action) {
            parts.push(`action=${this.app.action.split(",")[1]}`);
        }
        return "#" + parts.join("&");
    }

    get app() {
        return this.props.app;
    }

    click_app_item(event) {
        this.state.active = true;
        this.menuService.selectMenu(this.app);
    }
}

AppItem.props = {
    app: {
        type: Object
    }
};

AppItem.template = "irie_backend_theme.app_bar_item";
