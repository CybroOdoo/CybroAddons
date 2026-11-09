/* @odoo-module */
import { session } from "@web/session";
import { useEnv } from "@web/owl2/utils";
import { Component } from "@odoo/owl";


import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {Counter} from "./editor_menu"



export class InfinitoSystrayItem extends Component {
    static template = "backend_theme_infinito.StudioSystray"

    setup() {

        this.env = useEnv();
        this.advancedPanel = useService("infinito_advanced_panel");
        this.action = useService("action");
        this.actionService = useService("action");
        this.mode = false;
        this.editor = useService("editor");
    }

    /**
     * Method to handle click event for Simple Editor
     */
    _onClickSimpleEditor() {
        this._onClickAdvancedEditor();
    }

    /**
     * Method to handle click event for Advanced Editor
     */
    _onClickAdvancedEditor() {
        this.advancedPanel.close();
        var navbar = document.querySelector(".o_main_navbar")
        if (navbar) {
            navbar.style.display = "none";
            this.editor.open();
        }
    }
}

// Exporting systrayItem
export const systrayItem = {
    Component: InfinitoSystrayItem,
    isDisplayed: () => Boolean(session.infinitoCanManageTheme),
};

// Definition of InfinitoSystrayAdv component
export class InfinitoSystrayAdv extends Component {
    static template = "backend_theme_infinito.AdvSystray"

    // Setup method to initialize component
    setup() {
        this.env = useEnv();
        this.advancedPanel = useService("infinito_advanced_panel");
        this.action = useService("action");
        this.dialog = useService("dialog");
    }

    _onClick() {
        return this.advancedPanel.open(Counter);
    }

}

export const InfinitoSystrayAdvItem = {
    Component: InfinitoSystrayAdv,
    isDisplayed: () => Boolean(session.infinitoCanManageTheme || session.userEdit),
};
registry.category("systray").add("backend_theme_infinito.infinito_systray", systrayItem, {sequence: 25})
    .add("backend_theme_infinito.infinito_systray_adv", InfinitoSystrayAdvItem, {sequence: 26})
