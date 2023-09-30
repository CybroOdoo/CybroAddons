/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import core from 'web.core';
const commandProviderRegistry = registry.category("command_provider");
const { onMounted } = owl;
import { patch } from 'web.utils';
var rpc = require('web.rpc');
patch(NavBar.prototype, 'jazzy_backend_theme/static/src/js/appMenu.js', {

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
        onMounted(this.onMounted);
    },
    fetch_data: function() {
        var self = this;
        rpc.query({model: 'res.config.settings',method: 'config_color_settings',args: [0],}).then(function(result){
            self.colors = result;
            if (result.primary_accent !== false){
                document.documentElement.style.setProperty("--primary-accent",result.primary_accent);
            }
            if (result.appbar_color !== false){
                document.documentElement.style.setProperty("--app-bar-accent",result.appbar_color);}
            if (result.primary_hover !== false){
                document.documentElement.style.setProperty("--primary-hover",result.primary_hover);}
            if (result.full_bg_img !== false) {
                var imageUrl = 'url(data:image/png;base64,' + result.full_bg_img + ')';
                var appComponentsDivs = document.getElementsByClassName('app_components');
                for (var i = 0; i < appComponentsDivs.length; i++) {
                    appComponentsDivs[i].style.backgroundImage = imageUrl;
                }
            }
            if (result.appbar_text !== false){
                document.documentElement.style.setProperty("--app-menu-font-color",result.appbar_text);}
            if (result.secondary_hover !== false){
                document.documentElement.style.setProperty("--secondary-hover",result.secondary_hover);}
            if (result.kanban_bg_color !== false) {
                document.documentElement.style.setProperty("--kanban-bg-color", result.kanban_bg_color);
            }
        });
    },
    onMounted() {
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
                "jazzy_backend_theme.SearchResults",
                {
                    results: results,
                    widget: this,
                }
            )
        );
    },
    OnClickMainMenu() {
        if ($('.app_components').css("display") === "none") {
            $('.app_components').fadeIn(250);
            $('.o_menu_sections').attr('style','display: none !important');
            $('.o_menu_brand').attr('style','display: none !important');
            $('.o_action_manager').attr('style','display: none !important');
            $('.sidebar_panel').attr('style','display: none !important');
        } else {
            $('.app_components').fadeOut(50);
            $('.o_menu_sections').attr('style','display: flex !important');
            $('.o_menu_brand').attr('style','display: block !important');
            $('.o_action_manager').attr('style','display: block !important');
            $('.sidebar_panel').attr('style','display: block !important');
        }
    },
    onNavBarDropdownItemSelection(app) {
    var appComponentsDiv = document.querySelector('.app_components');
    appComponentsDiv.style.display = 'none';
    $('.o_action_manager').attr('style','display: block !important');
    $('.sidebar_panel').attr('style','display: block !important');
    $('.o_menu_brand').attr('style','display: flex !important');
    $('.o_menu_sections').attr('style','display: flex !important');
    this._super(app);
}
});