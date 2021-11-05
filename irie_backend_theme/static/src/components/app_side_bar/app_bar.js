/** @odoo-module **/

const { Component, hooks } = owl;
const { useExternalListener, useState, useRef } = hooks;
import { useService } from "@web/core/utils/hooks";
import { bus, _t } from 'web.core';
import { AppItem } from "./app_bar_item";

export class AppBar extends Component {
    setup(){
        this.currentAppSectionsExtra = [];
        this.actionService = useService("action");
        this.menuService = useService("menu");
        var apps = this.menuService.getApps();
        this.state = useState({ apps });

    }
    willUnmount() {
        this.env.bus.off("MENUS:APP-CHANGED", this);
    }

}
 AppBar.components = { AppItem };
 AppBar.props = {};
 AppBar.template = 'irie_backend_theme.app_bar';