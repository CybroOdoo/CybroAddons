/* @odoo-module */
// Importing necessary modules and components
import { Component,useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Counter } from "./editor_menu"
import { EditorClientAction } from "./editor_client_action"
const { onMounted, mount,useEnv } = owl
// Definition of InfinitoSystrayItem component
export class InfinitoSystrayItem extends Component{
    static template="backend_theme_infinito.StudioSystray"
    // Setup method to initialize component
    setup(){
        this.render();
        this.env= useEnv();
        this.action = useService("action");
        this.actionService = useService("action");
        this.mode = false;
        this.editor = useService("editor");
    }
     /**
     * Method to handle click event for Simple Editor
     */
    _onClickSimpleEditor(){
         var $el = $('body')
    }
     /**
     * Method to handle click event for Advanced Editor
     */
    _onClickAdvancedEditor(){
          var navbar= document.querySelector(".o_main_navbar")
          if (navbar) {
            navbar.style.display = "none";
            this.editor.open();
          }
    }
}
// Exporting systrayItem
export const systrayItem = {
    Component: InfinitoSystrayItem,
};
// Definition of InfinitoSystrayAdv component
export class InfinitoSystrayAdv extends Component{
    static template="backend_theme_infinito.AdvSystray"
     // Setup method to initialize component
    setup(){
        this.env= useEnv();
        this.action = useService("action");
        this.dialog = useService("dialog");
    }
     /**
     * Method to handle click event for Advanced Systray
     */
    _onClick(){
          var env= this.env;
          var dialog = this.dialog;
          mount(Counter, document.body,{env,dialog});
    }
}
// Exporting InfinitoSystrayAdvItem
export const InfinitoSystrayAdvItem={
    Component: InfinitoSystrayAdv,
};
// Adding components to registry
registry.category("systray").add("backend_theme_infinito.infinito_systray",systrayItem, {sequence:25})
                            .add("backend_theme_infinito.infinito_systray_adv",InfinitoSystrayAdvItem,{sequence:26})
