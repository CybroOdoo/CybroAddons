/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useService } from "@web/core/utils/hooks";
const commandProviderRegistry = registry.category("command_provider");
import { useRef, onMounted, useSubEnv } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    // To modify the Navbar properties and functions.
    setup() {
        super.setup()
        var self = this;
        this._search_def = $.Deferred();
        let { apps, menuItems } = computeAppsAndMenuItems
            (this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        this.fetch_data();
        this.search_container = useRef('search_container');
        this.search_input = useRef('search_input');
        this.app_menu = useRef('app_menu');
        this.search_results = useRef('search_results');
        onMounted(() => {
            this.setClass();
        })
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
    setClass() {
        // Set variable for html elements.
        this.$search_container = $(this.search_container.el)
        this.$search_input = $(this.search_input.el);
        this.$search_results = $(this.search_results.el);
        this.$app_menu = $(this.app_menu.el);
        this.$dropdown_menu = $(this.search_container.el.parentElement);
    },
    _searchMenusSchedule() {
        // Hide / Show based on search input.
        this.$search_results.removeClass("o_hidden")
        this.$app_menu.addClass("o_hidden");
        this._search_def.reject();
        this._search_def = $.Deferred();
        setTimeout(this._search_def.resolve.bind(this._search_def), 50);
        this._search_def.done(this._searchMenus.bind(this));
    },
    _searchMenus() {
        // App menu search function
        var query = this.$search_input.val();
        if (query === "") {
            this.$search_container.removeClass("has-results");
            this.$app_menu.removeClass("o_hidden");
            this.$search_results.empty();
            return;
        }
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
        this.$search_container.toggleClass(
            "has-results",
            Boolean(results.length)
        );
        this.$search_results.empty()
        var resultsHtml = ""
        results.forEach(function(result) {
            resultsHtml += "<p><a href='odoo/action-" + result["actionID"]+
            "'>" + result["name"] + "</a></p>"
        })
        this.$search_results.append(resultsHtml);
    },
    onAppClick(app) {
        this.onNavBarDropdownItemSelection(app);
    }
})
