/** @odoo-module **/
/**
 * Imports necessary modules and dependencies for the component.
 */
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { Component } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

/**
 * Component for handling language switching in the system tray.
 * Displays a dropdown menu to select the language and triggers a reload after changing the language.
 */
export class LanguageSwitch extends Component {
    setup() {
        this.currentLang = session.currentLang;
        this.availableLanguages = session.availableLanguages;
    }
    /**
     * Toggles the language when a language is selected from the dropdown.
     * Updates the user's language setting and triggers a reload to apply the changes.
     * @param {string} lang - The selected language code.
     * @returns {void}
     */
     toggleLang(lang) {
        rpc('/theme_studio_plus/set_user_lang', { lang }).then(async () => {
            await this.env.bus.trigger("MENUS:APP-CHANGED");
            location.reload();
        });
    }
}
LanguageSwitch.template = "backend_theme_infinito_plus.LanguageSwitch";
LanguageSwitch.components = { Dropdown, DropdownItem };
LanguageSwitch.toggleDelay = 1000;
/**
 * Systray item configuration for the language switch component.
 */
export const systrayItem = {
    Component: LanguageSwitch,
};
// Adding the language switch component to the systray category with a specific sequence
registry.category("systray").add("LanguageSwitch", systrayItem, { sequence: 29 });