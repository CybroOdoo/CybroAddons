/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { EditorMenu } from "./editor_menu"
import { ThemeEditorSidebar } from "./theme_editor_sidebar"
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ThemeStudioWidget } from "./ThemeStudioWidget";
const { onMounted, mount, useEnv } = owl
/**
 * EditorClientAction class handles client actions for theme editing.
 */
export class EditorClientAction extends Component{
     /**
     * Sets up the initial state and environment for the EditorClientAction component.
     */
        setup(){
            super.setup();
            this.env= useEnv();
            this.dialog = useService("dialog");
            var navbar= document.querySelector(".o_main_navbar")
            if (navbar) {
                navbar.style.display = "none";
            }
            this.state=useState({
                menus:false,
                viewType:'tree',
            })
            this.state.menus = [{
                id:1,
                name: 'Views',
                children: [{
                    'name': 'Tree/List',
                    'selector': 'tree',
                },
                {
                    'name': 'Form',
                    'selector': 'form',
                },
                {
                    'name': 'Kanban',
                    'selector': 'kanban',
                },
                {
                    'name': 'Control Panel',
                    'selector': 'control_panel',
                }],
            }, {
                id:2,
                name: 'UI Elements',
                children: [{
                   'name': 'Button',
                   'selector': 'button',
                },
               {
                  'name': 'Progress Bar',
                  'selector': 'progress_bar',
               },
               {
                  'name': 'Tab',
                  'selector': 'tab',
               },
                {
                   'name': 'Input',
                   'selector': 'input',
                },
                {
                   'name': 'Search',
                   'selector': 'search',
                },
                {
                   'name': 'Misc',
                   'selector': 'misc',
                },],
            }
        ];
        }
        /**
         * Handles button click event to switch between view types.
         * @param {Event} ev - The click event object.
         */
        _onButtonClick(ev){
            ev.preventDefault();
            var mode = ev.currentTarget.id;
            this.state.viewType=mode;
        }
        /**
         * Handles item click event in the menu.
         * @param {Event} ev - The click event object.
         */
        onItemClick(ev){
            var object = ev
            var elem_name = ev.currentTarget.dataset.name
            var preset = ev.target.dataset.preset
            var env= this.env;
            var dialog = this.dialog;
            ev.stopPropagation();
            this.sidebar_pos = document.querySelector('.backend_theme_studio_sidebar .sidebar-here')
            var sidebars=document.querySelector('.marg_main')
            if (sidebars){
                sidebars.style.marginLeft="340px";
            }else{
                sidebars.style.marginLeft="0px";
            }
            mount(ThemeEditorSidebar,document.body,{env,dialog, props:{elem_name,preset,object}})
        }
        /**
         * Handles the event when the theme studio sidebar is closed.
         * @param {Event} ev - The click event object.
         */
        _onThemeStudioClose(ev){
            ev.preventDefault();
            window.location.href = '/web'
        }
         /**
         * Handles the event when the reset button is clicked to reset to default settings.
         * @param {Event} ev - The click event object.
         */
        _onResetClick(ev){
             jsonrpc('/theme_studio/reset_to_default',  {
                method:'call',
            });
            this.setAssets();
            location.reload();
        }
         /**
         * Toggles the sidebar visibility.
         * @param {Event} ev - The click event object.
         */
        _onThemeStudioToggleSidebar (ev) {
           ev.currentTarget.classList.toggle('open');
           var main_div = document.querySelector('.marg_main');
           ev.preventDefault();
           if (document.querySelector(".open") && main_div){
                mount(EditorMenu, document.body);
                main_div.style.marginLeft="340px";
           }else{
                main_div.style.marginLeft="0px";
               document.querySelector(".sidebar_simple_editor").remove();
           }
        }
        /**
         * Sets the assets for the theme editor.
         */
        setAssets(){
            location.search = "?debug=assets";
        }
}
// Define the template for the EditorClientAction component
EditorClientAction.template = "backend_theme_infinito.ThemeStudioMenu";

// Register the EditorClientAction component in the actions registry
registry.category("actions").add("backend_theme_infinito.editor_client_action",EditorClientAction);
