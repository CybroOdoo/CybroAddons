/** @odoo-module **/
import { Sidebar } from "./Sidebar";
import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { useState,useRef } from "@odoo/owl";
import { EditorClientAction } from "@backend_theme_infinito/js/editor_client_action"
import { patch } from "@web/core/utils/patch";
const { mount, onPatched, xml } = owl;
import { _t } from "@web/core/l10n/translation";
/**
 * Class representing advanced features sidebar.
 * Extends the Sidebar class.
 */
export class AdvancedFeatures extends Sidebar{
    static template = xml` <t t-name="backend_theme_infinito.sidebar_simple_editor">
        <div class="sidebar_simple_editor">
            <Sidebar/>
        </div>
    </t>`;
    static components = { Sidebar };
}
// Patching EditorClientAction prototype
patch(EditorClientAction.prototype,{
     /**
     * Handles the toggle sidebar event.
     * Toggles the sidebar visibility.
     * @param {Event} ev - The event object.
     */
    _onThemeStudioToggleSidebar(ev){
        ev.currentTarget.classList.toggle('open');
        var main_div = document.querySelector('.marg_main');
        ev.preventDefault();
        if (document.querySelector(".open") && main_div){
            mount(AdvancedFeatures, document.body);
            main_div.style.marginLeft="340px";
        }else{
            main_div.style.marginLeft="0px";
            document.querySelector(".sidebar_simple_editor").remove();
        }
    }
})
