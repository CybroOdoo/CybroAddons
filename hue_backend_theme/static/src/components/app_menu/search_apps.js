/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import core from 'web.core';

const commandProviderRegistry = registry.category("command_provider");

import { patch } from 'web.utils';
var rpc = require('web.rpc');
patch(NavBar.prototype, 'hue_backend_theme/static/src/js/appMenu.js', {

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
        this.colors = this.fetch_data();
    },
    fetch_data: function() {
        var self = this;
        rpc.query({model: 'res.config.settings',method: 'config_color_settings',args: [0],}).then(function(result){
            self.colors = result;
            console.log("$$$",result);
            if (result.primary_accent !== false){
                document.documentElement.style.setProperty("--primary-accent",result.primary_accent);
            }
            if (result.appbar_color !== false){
                document.documentElement.style.setProperty("--app-bar-accent",result.appbar_color);}
            if (result.primary_hover !== false){
                document.documentElement.style.setProperty("--primary-hover",result.primary_hover);}
            if (result.secondary_color !== false){
                document.documentElement.style.setProperty("--primary-accent-border",result.secondary_color);}
            if (result.full_bg_img !== false){
                document.documentElement.style.setProperty("--full-screen-bg",'url(data:image/png;base64,'+result.full_bg_img+')');
                console.log(result.full_bg_img);

            }
            if (result.appbar_text !== false){
                document.documentElement.style.setProperty("--app-menu-font-color",result.appbar_text);}
            if (result.secoundary_hover !== false){
                document.documentElement.style.setProperty("--secoundary-hover",result.secoundary_hover);}
            if (result.kanban_bg_color !== false){
                document.documentElement.style.setProperty("--kanban-bg-color",result.kanban_bg_color);}
        });
    },

    mounted() {
        this._super();
        this.$search_container = $(".search-container");
        this.$search_input = $(".search-input input");
        this.$search_results = $(".search-results");
        this.$app_menu = $(".app-menu");
        this.$dropdown_menu = $(".dropdown-menu");
    },

     _searchMenusSchedule: function () {
        this.$search_results.removeClass("o_hidden")
        this.$app_menu.addClass("o_hidden");
        this._search_def.reject();
        this._search_def = $.Deferred();
        setTimeout(this._search_def.resolve.bind(this._search_def), 50);
        this._search_def.done(this._searchMenus.bind(this));
    },

    _searchMenus: function () {
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
        this.$search_results.html(
            core.qweb.render(
                "hue_backend_theme.SearchResults",
                {
                    results: results,
                    widget: this,
                }
            )
        );
    },

});