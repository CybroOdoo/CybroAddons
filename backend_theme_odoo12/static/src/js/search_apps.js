/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
const { onMounted, useState, useRef } = owl;
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        // Attach a ref for the root element
        this.searchState = useState({
            searchResults: [],
            hasResults: false,
            showResults: false,
            query: ""
        });
        this.searchInputRef = useRef("searchInput");
        this._searchTimeout = null;
        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
    },

    openSidebar(ev) {
        const sidebarPanel = ev.target.closest('header').querySelector('#sidebar_panel');
        const actionManager = document.body.querySelector('.o_action_manager');
        if (!ev.target.classList.contains('opened')) {
            sidebarPanel.style.display = 'block';
            ev.target.classList.toggle('opened');
            actionManager.style.marginLeft = '320px';
            actionManager.style.transition = 'all .1s linear';
        } else {
            sidebarPanel.style.display = 'none';
            ev.target.classList.toggle('opened');
            actionManager.style.marginLeft = '0px';
        }
    },
    clickSidebar(ev) {
        this.searchState.query = "";
        this.searchInputRef.el.value = "";
        this.searchState.searchResults = [];
        this.searchState.hasResults = false;
        this.searchState.showResults = false;
        const sidebarPanel = ev.target.closest('header').querySelector('#sidebar_panel');
        const actionManager = document.body.querySelector('.o_action_manager');
        sidebarPanel.style.display = 'none';
        actionManager.style.marginLeft = '0px';
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

    getMenuUrl(actionID, menuId) {
        return `/web#action=${actionID}&menu_id=${menuId}`;
    },
});
