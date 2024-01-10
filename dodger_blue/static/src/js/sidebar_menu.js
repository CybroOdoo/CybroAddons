/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";


patch(NavBar.prototype,{

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
     setup() {
        super.setup()
        this._search_def = $.Deferred();
        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        this.user_id = session.uid;
        this.session = session;
        onMounted(this.onMounted);
     },

      onMounted() {
        this.$search_container = $(".search-container");
        this.$search_input = $(".search-input input");
        this.$search_results = $(".search-results");
        this.$app_menu = $(".app-menu");
        this.$dropdown_menu = $(".dropdown-menu");
        this.$cybro_main_menu = $(".cybro-main-menu")
        var navbar = $(".o_main_navbar")
        var self = this;
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
        var resultsHtml = ""
        this.$search_results.empty();
        results.forEach(function(result) {
            resultsHtml += "<div class='search_icons'><a class='o-menu-search-result dropdown-item col-12 ml-auto mr-auto'  style=\"background-image:url('data:image/png;base64," + result["webIconData"] + "')\" href='web#action=" + result["actionID"] + "&menu_id=" + result["id"] + "'>" + result["name"] + "</a></div>"
        })
        this.$search_results.append(resultsHtml);
    },
 });
