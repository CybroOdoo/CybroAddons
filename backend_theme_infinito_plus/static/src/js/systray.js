/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import session from "web.session";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
export class LanguageSwitch extends Component {
    setup() {
        this.currentLang = session.currentLang;
        this.availableLanguages = session.availableLanguages;
        this.orm = useService("orm");
    }
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
export const systrayItem = {
    Component: LanguageSwitch,
};
registry.category("systray").add("LanguageSwitch", systrayItem, { sequence: 1 });
