/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import core from 'web.core';
// patch NavaBar for searching apps and contents by extending navbar
import { patch } from 'web.utils';
patch(NavBar.prototype, 'backend_theme_odoo12/static/src/js/search_apps.js', {
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------
    /**
     * @override
     */
     setup() {
        this._super();
        this._search_def = $.Deferred();
        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
    },
    mounted() {
        this._super();
        console.log(this)
        this.$search_container = this.el?.querySelector(".search-container");
        this.$search_input =  this.$search_container?.querySelector(".search-input input");
        this.$search_results =  this.$search_container?.querySelector(".search-results");
        this.$dropdown_menu =  this.$search_container?.querySelector(".dropdown-menu");
    },
    /**
     * Shows the search results and triggers a search.
     */
     _searchMenusSchedule: function () {
        this.$search_results.classList.remove("o_hidden")
        this._search_def.reject();
        this._search_def = $.Deferred();
        setTimeout(this._search_def.resolve.bind(this._search_def), 50);
        this._search_def.done(this._searchMenus.bind(this));
    },
     /**
     * Performs a fuzzy search on the available apps and menu items.
     */
    _searchMenus: function () {
        var query = this.$search_input.value;
        if (query === "") {
            this.$search_container.classList.remove("has-results");
            this.$search_results.innerHTML = '';
            return;
        }
        // search for all apps
        var results = [];
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
          // Search for all menu items.
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
        // Render the search results.
        this.$search_container.classList.toggle("has-results",Boolean(results.length));
        let htmlContent =  core.qweb.render(
                "backend_theme_odoo12.SearchResults",
                {
                    results: results,
                    widget: this,
                })
        this.$search_results.innerHTML = htmlContent
    },
});
