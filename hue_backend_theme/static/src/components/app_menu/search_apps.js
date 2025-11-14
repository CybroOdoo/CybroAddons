/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useService } from "@web/core/utils/hooks";
import { useRef, onMounted, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    // To modify the Navbar properties and functions.
    setup() {
        super.setup()
        var self = this;
        this.searchState = useState({
            searchResults: [],
            hasResults: false,
            showResults: false,
            query: ""
        });

        this.fetch_data();
        this.searchInputRef = useRef("searchInput");
        this._searchTimeout = null;

        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
    },

    async fetch_data() {
        // To fetch colors from database.
        this.orm = useService("orm")
        var result = await this.orm.call("res.config.settings",
            "config_color_settings", [0])
        if (result.primary_accent) {
            document.documentElement.style.setProperty("--primary-accent",
                result.primary_accent);
        }
        if (result.appbar_hover !== false){
            document.documentElement.style.setProperty("--appbar-hover",
                result.appbar_hover);
        }
        if (result.appbar_color !== false){
            document.documentElement.style.setProperty("--app-bar-accent",
                result.appbar_color);
        }
        if (result.primary_hover !== false){
            document.documentElement.style.setProperty("--primary-hover",
                result.primary_hover);
        }
        if (result.full_bg_img !== false){
            document.documentElement.style.setProperty("--full-screen-bg",
            'url(data:image/png;base64,'+result.full_bg_img+')');
        }
        if (result.appbar_text !== false){
            document.documentElement.style.setProperty("--app-menu-font-color",
                result.appbar_text);
        }
        if (result.kanban_bg_color !== false){
            document.documentElement.style.setProperty("--kanban-bg-color",
                result.kanban_bg_color);
        }
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
                actionID: menu.actionID,
                id: menu.id,
            });
        });

        this.searchState.searchResults = results;
        this.searchState.hasResults = results.length > 0;
    },

    onAppClick(app) {
        this.onNavBarDropdownItemSelection(app);
    },

    getMenuUrl(actionID, menuId) {
        return `/web#action=${actionID}&menu_id=${menuId}`;
    },

    webIconData(menu) {
        return `background-image:url('${menu?.webIconData}')`
    },

    onSearchResultClick(ev) {
        // Clear search after clicking a result
        this.searchState.query = "";
        this.searchInputRef.el.value = "";
        this.searchState.searchResults = [];
        this.searchState.hasResults = false;
        this.searchState.showResults = false;
    },
})
