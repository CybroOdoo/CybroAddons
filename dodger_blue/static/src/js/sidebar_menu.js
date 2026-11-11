/** @odoo-module **/

import { proxy } from "@odoo/owl";
import { fuzzyLookup } from "@web/core/utils/search";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { NavBar } from "@web/webclient/navbar/navbar";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.dodgerUser = user;
        this.dodgerSearch = proxy({ query: "" });
    },

    get dodgerSearchResults() {
        const query = this.dodgerSearch.query.trim();
        if (!query) {
            return [];
        }
        const { apps, menuItems } = computeAppsAndMenuItems(
            this.menuService.getMenuAsTree("root")
        );
        return fuzzyLookup(query, [...apps, ...menuItems], (menu) =>
            menu.parents ? `${menu.parents} / ${menu.label}` : menu.label
        );
    },

    onDodgerSearchInput(ev) {
        this.dodgerSearch.query = ev.target.value;
    },

    selectDodgerSearchResult(result) {
        this.onNavBarDropdownItemSelection(this.menuService.getMenu(result.id));
        this.dodgerSearch.query = "";
    },
});
