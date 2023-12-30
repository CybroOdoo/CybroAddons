/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useRef ,onMounted} from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

// patch NavaBar for searching apps and contents by extending navbar
patch(NavBar.prototype,  {
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------
    /**
     * @override
     */
    setup() {
            super.setup()
            this.side_root = useRef("side_root");
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
            this.$search_container = $(this.root.el.children.sidebar_panel.querySelector(".search-container"));
            this.$search_input = $(this.root.el.children.sidebar_panel.querySelector(".search-input input"));
            this.$search_results = $(this.root.el.children.sidebar_panel.querySelector(".search-results"));
            this.$app_menu = $(this.root.el.children.sidebar_panel.querySelector(".app-menu"));
    },
    /**
     * Shows the search results and triggers a search.
     */
    _searchMenusSchedule: function() {
            this.$search_results.removeClass("o_hidden")
            this.$app_menu.addClass("o_hidden");
            this._search_def.reject();
            this._search_def = $.Deferred();
            setTimeout(this._search_def.resolve.bind(this._search_def), 50);
            this._search_def.done(this._searchMenus.bind(this));
    },
    /**
     * Performs a fuzzy search on the available apps and menu items.
     */
    _searchMenus: function() {
        var query = this.$search_input.val();
        var self = this
        if (query === "") {
            this.$search_container.removeClass("has-results");
            this.$app_menu.removeClass("o_hidden");
            this.$search_results.empty();
            return;
        }
        // Search for all apps.
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
        this.$search_container.toggleClass("has-results", Boolean(results.length));
        this.$search_results.empty()
        var resultsHtml = ""
        results.forEach(function(result) {
            resultsHtml += "<div class='search_icons'><a class='o-menu-search-result dropdown-item col-12 ml-auto mr-auto'  style=\"background-image:url('data:image/png;base64," + result["webIconData"] + "')\" href='web#action=" + result["actionID"] + "&menu_id=" + result["id"] + "'>" + result["name"] + "</a></div>"
        })
        this.$search_results.append(resultsHtml);
        // close side bar panel on click
        let elements = this.$search_results[0].querySelectorAll('.search_icons')
        for (var i = 0; i < elements.length; i++) {
            elements[i].addEventListener('click', function(){
            var ev = self.__owl__.bdom.el.querySelectorAll('#openSidebar .fa')[0]
            var $el = $(self.__owl__.bdom.el.querySelectorAll('#sidebar_panel'))
            var action = $(self.__owl__.bdom.parentEl.querySelectorAll('.o_action_manager'))
            $el.find('.form-control')[0].value = ""
            self._searchMenus()
            if (!$(ev).hasClass('opened')){
                $el.show()
                $(ev).toggleClass('opened')
                $el.css({'display':'block'});
                action.css({'margin-left': '320px','transition':'all .1s linear'});
            }
            else{
                $el.hide()
                $(ev).toggleClass('opened')
                $el.css({'display':'none'});
                action.css({'margin-left': '0px'});
            }
            });
        }
    },
});
