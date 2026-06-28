/** @odoo-module **/
import { useService, useBus } from "@web/core/utils/hooks";
import { Component, onWillStart, useRef, useState } from "@odoo/owl";
import { session } from "@web/session";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";

export class SystrayWidget extends Component {
    async setup() {
        super.setup(...arguments);
        this.state = useState({
            inputfield: false,
            searchInput: '',
            result: []
        });
        this.orm = useService('orm');
        this.action = useService("action");
        this.menuService = useService("menu");
        this.add_fav = useRef("add_fav")
        this.dropList = useRef("dropList")
    }
    async click_fav(ev) {
        this.state.inputfield = true;
        this.add_fav.el.style.display = 'none'
    }
    async _onClick() {
        var self = this;
        var input = this.state.searchInput;
        this.state.result = await this.orm.call("ir.ui.menu", "search_read", [[['name', 'ilike', input], ['action', '!=', null]]]);
        if (this.dropList.el) {
            this.dropList.el.style.display = 'block'
        }
    }
    async click_view(menuId) {
        const id = parseInt(menuId);
        const menu = this.menuService.getMenu(id);
        if (menu) {
            await this.menuService.selectMenu(id);
        } else {
            console.warn(`Menu with ID ${id} not found in the current menu tree.`);
        }
        this.state.result = []
    }
    async _onClick_close(ev) {
        this.state.inputfield = false;
        this.add_fav.el.style.display = 'block'
    }
    async _onClick_clear(ev) {
        this.state.searchInput = '';
        if (this.dropList.el) {
            this.dropList.el.style.display = 'none'
        }
    }
}
SystrayWidget.components = { Dropdown };
export const systrayItem = {
    Component: SystrayWidget,
};
SystrayWidget.template = "systray_menu_favourites.SystrayShortcut"
registry.category("systray").add("SystrayMenu", systrayItem, { sequence: 0 });
