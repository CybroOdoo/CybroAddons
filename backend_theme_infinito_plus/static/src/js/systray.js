/** @odoo-module **/
/**
 * Imports necessary modules and dependencies for the component.
 */
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
/**
 * Component for handling language switching in the system tray.
 * Displays a dropdown menu to select the language and triggers a reload after changing the language.
 */
export class LanguageSwitch extends Component {
    setup() {
        this.currentLang = session.currentLang;
        this.availableLanguages = session.availableLanguages;
        this.orm = useService("orm");
    }
    /**
     * Toggles the language when a language is selected from the dropdown.
     * Updates the user's language setting and triggers a reload to apply the changes.
     * @param {string} lang - The selected language code.
     * @returns {void}
     */
     toggleLang(lang) {
        this.orm.write('res.users', [session.uid], {lang}).then(async () => {
            await this.env.bus.trigger("MENUS:APP-CHANGED");
            location.reload();
        });
    }
}
LanguageSwitch.template = "LanguageSwitch";
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
