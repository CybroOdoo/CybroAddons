/** @odoo-module */
import {NavBar} from "@web/webclient/navbar/navbar";
import {registry} from "@web/core/registry";
const {fuzzyLookup} = require('@web/core/utils/search');
import {computeAppsAndMenuItems} from "@web/webclient/menus/menu_helpers";
import core from 'web.core';
const {onMounted} = owl;
import {patch} from 'web.utils';

// patch NavaBar for searching apps and contents by extending navbar
patch(NavBar.prototype, 'multicolor_backend_theme/static/src/js/search_apps.js', {
    //--------------------------------------------------------------------------
    // Public
    // For advance search bar feature, and this will enable a global search for apps and related content
    //--------------------------------------------------------------------------
    /**
     * @override
     */
    setup() {
        this._super();
        this._search_def = $.Deferred();
        let {
            apps,
            menuItems
        } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        onMounted(this.onMounted);
    },
    onMounted() {
        this.$search_container = $(".search-container");
        this.$search_input = $(".search-input input");
        this.$search_results = $(".search-results");
        this.$app_menu = $(".app-menu");
        this.$dropdown_menu = $(".dropdown-menu");
    },
    // to show the search results
    _searchMenusSchedule: function() {
        this.$search_results.removeClass("o_hidden")
        this.$app_menu.addClass("o_hidden");
        this._search_def.reject();
        this._search_def = $.Deferred();
        setTimeout(this._search_def.resolve.bind(this._search_def), 50);
        this._search_def.done(this._searchMenus.bind(this));
    },
    // function for searching all apps and content
    _searchMenus: function() {
        var query = this.$search_input.val();
        if (query === "") {
            this.$search_container.removeClass("has-results");
            this.$app_menu.removeClass("o_hidden");
            this.$search_results.empty();
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
        // search for all content
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
        this.$search_container.toggleClass("has-results", Boolean(results.length));
        this.$search_results.html(core.qweb.render("multicolor_backend_theme.SearchResults", {
            results: results,
            widget: this,
        }));
    },
});
