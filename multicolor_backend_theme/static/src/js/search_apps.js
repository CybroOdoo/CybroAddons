/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { fuzzyLookup } from "@web/core/utils/search";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { proxy, onWillDestroy } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    setup() {
        super.setup();

        this.searchState = proxy({
            searchResults: [],
            hasResults: false,
            showResults: false,
            query: ""
        });

        onWillDestroy(() => clearTimeout(this._searchTimeout));
        this._searchTimeout = null;

        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
    },

    _searchMenusSchedule(ev) {
        const query = ev.target.value;
        this.searchState.query = query;

        // Clear previous timeout
        if (this._searchTimeout) {
            clearTimeout(this._searchTimeout);
        }

        // Debounce search
        this._searchTimeout = setTimeout(() => {
            this._searchMenus(query);
        }, 50);
    },

    _searchMenus(query) {
        if (query === "") {
            this.searchState.searchResults = [];
            this.searchState.hasResults = false;
            this.searchState.showResults = false;
            return;
        }

        this.searchState.showResults = true;
        var results = [];

        // Search for all apps
        fuzzyLookup(query, this._apps, (menu) => menu.label)
            .forEach((menu) => {
                results.push({
                    category: "apps",
                    name: menu.label,
                    href: menu.href,
                    actionID: menu.actionID,
                    id: menu.id,
                    webIconData: menu.webIconData,
                });
            });

        // Search for all content
        fuzzyLookup(query, this._searchableMenus, (menu) =>
            (menu.parents + " / " + menu.label).split("/").reverse().join("/")
        ).forEach((menu) => {
            results.push({
                category: "menu_items",
                name: menu.parents + " / " + menu.label,
                href: menu.href,
                actionID: menu.actionID,
                id: menu.id,
            });
        });

        this.searchState.searchResults = results;
        this.searchState.hasResults = results.length > 0;
    },

    async onSearchResultClick(ev, result) {
        ev.preventDefault();
        await this.menuService.selectMenu(result.id);
        this.searchState.query = "";
        this._searchMenus("");
        this.onclickCloseSidebar();
    }
});
