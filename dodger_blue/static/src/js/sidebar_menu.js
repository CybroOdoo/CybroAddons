/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import core from 'web.core';

const commandProviderRegistry = registry.category("command_provider");
const {  onMounted } = owl;

import { patch } from 'web.utils';
var rpc = require('web.rpc');
var session = require('web.session');
console.log("session",session)


patch(NavBar.prototype, 'dodger_blue/static/src/js/sidebar_menu.js', {

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
        this.user_id = session.uid;
        this.session = session;
        onMounted(this.onMounted);
     },

      onMounted() {
        console.log("this:",this)
        this.$search_container = $(".search-container");
        this.$search_input = $(".search-input input");
        console.log(this.$search_input,'kkkkkkkkkkkkkk')

        this.$search_results = $(".search-results");
        this.$app_menu = $(".app-menu");
        this.$dropdown_menu = $(".dropdown-menu");
        this.$cybro_main_menu = $(".cybro-main-menu")

//        this.$cybro_main_menu.removeClass("show")

        var navbar = $(".o_main_navbar")
        var self = this;
        console.log(this.$search_results,'search results')
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
                "dodger_blue.SearchResults",
                {
                    results: results,
                    widget: this,

                }

            )
        );
    },

 });


































//odoo.define('dodger_blue.sidebar', function (require) {
//    'use strict';
//
//    var AppsMenu = require("web.AppsMenu");
//    var core = require('web.core');
//    var QWeb = core.qweb;
//    var session = require('web.session');
//
//    AppsMenu.include({
//        init: function (parent, menuData) {
//            this.user_id = session.uid;
//            this.session = session;
//            this._super.apply(this, arguments);
//            console.log(this._apps[0].web_icon_data,"this")
//            var sidebar = QWeb.render('AppsMenuSidebar',{
//                widget:this
//            });
//            $('.cybro-sidebar').html(sidebar);
//        }
//    });
//});
