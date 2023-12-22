/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useService } from "@web/core/utils/hooks";
const commandProviderRegistry = registry.category("command_provider");
const { onMounted } = owl;
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    // To modify the Navbar properties and functions.
    setup() {
        super.setup()
        var self = this
        this._search_def = $.Deferred();
        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        this.fetch_data()
        onMounted(() => {
            this.setClass()
        })
    },
    async fetch_data() {
        // To fetch colors from database.
        this.orm = useService("orm")
        var result = await this.orm.call("res.config.settings", "config_color_settings", [0])
        if (result.primary_accent !== false){
            document.documentElement.style.setProperty("--primary-accent",result.primary_accent)
        }
        if (result.appbar_color !== false){
            document.documentElement.style.setProperty("--app-bar-accent",result.appbar_color)
        }
        if (result.primary_hover !== false){
            document.documentElement.style.setProperty("--primary-hover",result.primary_hover)
        }
        if (result.full_bg_img !== false) {
            var imageUrl = 'url(data:image/png;base64,' + result.full_bg_img + ')';
            var appComponentsDivs = document.getElementsByClassName('app_components');
            for (var i = 0; i < appComponentsDivs.length; i++) {
                appComponentsDivs[i].style.backgroundImage = imageUrl;
            }
        }
        if (result.appbar_text !== false){
            document.documentElement.style.setProperty("--app-menu-font-color",result.appbar_text)
        }
        if (result.secondary_hover !== false){
            document.documentElement.style.setProperty("--secondary-hover",result.secondary_hover)
        }
        if (result.kanban_bg_color !== false) {
            document.documentElement.style.setProperty("--kanban-bg-color", result.kanban_bg_color)
        }
    },
    setClass() {
        // Set variable for html elements.
        this.$search_container = $(".search-container");
        this.$search_input = $(".search-input input");
        this.$search_results = $(".search-results");
        this.$app_menu = $(".app-menu");
        this.$dropdown_menu = $(".dropdown-menu");
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
            resultsHtml += "<p class='result-item'><a href='web#action=" + result["actionID"] + "&menu_id=" + result["id"] + "'>" + result["name"] + "</a></p>"
        })
        this.$search_results.append(resultsHtml);
        const resultItems = document.querySelectorAll('.result-item');
        resultItems.forEach(resultItem => {
            resultItem.addEventListener('click', function() {
                var appComponentsDiv = document.querySelector('.app_components');
                appComponentsDiv.style.display = 'none';
                $('.o_action_manager').attr('style','display: block !important');
                $('.sidebar_panel').attr('style','display: block !important');
                $('.o_menu_brand').attr('style','display: flex !important');
                $('.o_menu_sections').attr('style','display: flex !important');
            });
        });
    },
    OnClickMainMenu() {
        // To show search screen
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
        // To go to app menu
        var appComponentsDiv = document.querySelector('.app_components');
        appComponentsDiv.style.display = 'none';
        $('.o_action_manager').attr('style','display: block !important');
        $('.sidebar_panel').attr('style','display: block !important');
        $('.o_menu_brand').attr('style','display: flex !important');
        $('.o_menu_sections').attr('style','display: flex !important');
        if (app) {
            this.menuService.selectMenu(app);
        }
    },
})
