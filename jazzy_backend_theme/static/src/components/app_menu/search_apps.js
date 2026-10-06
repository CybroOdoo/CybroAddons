/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { fuzzyLookup } from "@web/core/utils/search";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useBus, useService } from "@web/core/utils/hooks";
import { onMounted, signal } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { router } from "@web/core/browser/router";
import { WebClient } from "@web/webclient/webclient";
import { registry } from "@web/core/registry";

// Keep the underlying app route so the Home button can return to it, but do
// not restore that action while the URL explicitly points to the app drawer.
patch(WebClient.prototype, {
    async loadRouterState() {
        const home = Boolean(router.current.jazzy_home);
        this.env.bus.trigger("JAZZY:HOME-CHANGED", home);
        if (!home) {
            return super.loadRouterState(...arguments);
        }
    },
});

patch(NavBar.prototype, {
    // To modify the Navbar properties and functions.
    setup() {
        super.setup()
        this.jazzyHomeVisible = signal(Boolean(router.current.jazzy_home));
        this._search_def = this.createDeferred();
        this.search_container = signal.ref();
        this.search_input = signal.ref();
        this.search_result = signal.ref();
        this.menuService = useService("menu");
        this.app_menu = signal.ref();
        this.sidebar_panel = signal.ref();
        this.app_components = signal.ref();
        Object.assign(this.state, { menus: [] });
        this.searchQuery = signal("");
        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        useBus(this.env.bus, "JAZZY:HOME-CHANGED", ({ detail: home }) => {
            this.setJazzyHomeVisible(home);
        });
        this.fetch_data()
        onMounted(() => {
            this.setClass();
            this.setJazzyHomeVisible(Boolean(router.current.jazzy_home));
        })
    },
    createDeferred() {
    let deferred = {};

    deferred.promise = new Promise((resolve, reject) => {
        deferred.resolve = resolve;
        deferred.reject = reject;
    });

    return deferred;
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
        if (result.full_bg_img) {
            const imageUrl = 'url("data:image/png;base64,' + result.full_bg_img + '")';
            document.documentElement.style.setProperty("--full-screen-bg", imageUrl);
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
        this.$search_container = this.search_container;
        this.$search_input = this.search_input;
        this.$search_results = this.search_result;
        this.$app_menu = this.app_menu;
    },
    _searchMenusSchedule() {
        this.$search_results().classList.remove("o_hidden");
        this.$app_menu().classList.add("o_hidden");
        this._search_def = this.createDeferred();
        this._searchMenus();
    },
    _searchMenus() {
        // App menu search function
        var query = this.searchQuery();
        if (query === "") {
            this.$search_container().classList.remove("has-results");
            this.$search_results().classList.add("o_hidden")
            this.$app_menu().classList.remove("o_hidden");
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
        this.state.menus = results
    },
    get menus() {
        return this.state.menus
    },
    get jazzySystrayItems() {
        if (!this.jazzyHomeVisible()) {
            return this.systrayItems;
        }
        // Website overrides systrayItems while its preview is mounted. The
        // drawer needs the regular controls without destroying that preview.
        return registry.category("systray")
            .getEntries()
            .map(([key, value]) => ({ key, ...value }))
            .filter((item) =>
                "isDisplayed" in item ? this.scope.run(() => item.isDisplayed(this.env)) : true
            )
            .reverse();
    },
    handleClick(menu) {
        router.replaceState({ jazzy_home: undefined }, { sync: true });
        this.setJazzyHomeVisible(false);
        this.app_components().nextSibling.style.display = "block";
        this.app_components().style.display = "none";
        this.app_components().style.opacity = "0";

        this.sidebar_panel().style.display = "block";
        this.app_menu().classList.remove('o_hidden');

        let children = this.app_components().parentElement.children;
        let oNavbar = null;

        for (let i = 0; i < children.length; i++) {
            if (children[i].classList.contains('o_navbar')) {
                oNavbar = children[i];
                break;
            }
        }

        let navChild = oNavbar.children[0].children;
        for (let i = 0; i < navChild.length; i++) {
            if (navChild[i].classList.contains('o_menu_brand')) {
                navChild[i].classList.remove('d-none');
                navChild[i].classList.add('d-block');
            }
            if (navChild[i].classList.contains('o_menu_sections')) {
                navChild[i].classList.remove('d-none');
                navChild[i].classList.add('d-block');
            }
        }
        if (menu) {
            this.menuService.selectMenu(menu.id);
        }
    },
    setJazzyHomeVisible(home) {
        this.jazzyHomeVisible.set(home);
        const drawer = this.app_components();
        if (!drawer) {
            return;
        }
        drawer.style.display = home ? "block" : "none";
        drawer.style.opacity = home ? "1" : "0";
        const content = drawer.parentElement.querySelector(".o_action_manager");
        if (content) {
            content.style.display = home ? "none" : "";
        }
        this.sidebar_panel().style.display = home ? "none" : "block";
        for (const section of drawer.parentElement.querySelectorAll(
            ".o_main_navbar .o_menu_brand, .o_main_navbar .o_menu_sections"
        )) {
            section.classList.toggle("d-none", home);
        }
    },
    async OnClickMainMenu() {
        const home = !router.current.jazzy_home;
        router.pushState({ jazzy_home: home ? true : undefined }, { sync: true });
        this.setJazzyHomeVisible(home);
        if (!home && !this.actionService.currentController) {
            await this.actionService.loadState();
        }
    },
    onNavBarDropdownItemSelection(app) {
        router.replaceState({ jazzy_home: undefined }, { sync: true });
        this.setJazzyHomeVisible(false);
        // To go to app menu
        this.app_components().style.display = "none";
        this.app_components().style.opacity = "0";
        this.app_components().nextSibling.style.display = "block"
        this.sidebar_panel().style.display = "block"
        let children = this.app_components().parentElement.children;
            let oNavbar = null;
            for (let i = 0; i < children.length; i++) {
                if (children[i].classList.contains('o_navbar')) {
                    oNavbar = children[i];
                    break;
                }
            }
            let navChild = oNavbar.children[0].children
            for (let i = 0; i < navChild.length; i++) {
                if (navChild[i].classList.contains('o_menu_brand')) {
                    navChild[i].classList.add('d-flex')
                    navChild[i].classList.remove('d-none')
                }
                if (navChild[i].classList.contains('o_menu_sections')) {
                    navChild[i].classList.add('d-flex')
                    navChild[i].classList.remove('d-none')
                }
            }
        if (app) {
            this.menuService.selectMenu(app);
        }
    },
    refreshNavBar() {
        // Find the navbar element
        let children = this.app_components().parentElement.children;
        let oNavbar = null;

        // Locate the navbar component
        for (let i = 0; i < children.length; i++) {
            if (children[i].classList.contains('o_navbar')) {
                oNavbar = children[i];
                break;
            }
        }

        if (oNavbar) {
            let navChild = oNavbar.children[0].children;
            // Ensure the navbar sections are displayed correctly
            for (let i = 0; i < navChild.length; i++) {
                if (navChild[i].classList.contains('o_menu_brand')) {
                    navChild[i].classList.remove('d-none');
                    navChild[i].classList.add('d-block');
                }
                if (navChild[i].classList.contains('o_menu_sections')) {
                    navChild[i].classList.remove('d-none');
                    navChild[i].classList.add('d-block');
                }
            }
        }
    }
})
