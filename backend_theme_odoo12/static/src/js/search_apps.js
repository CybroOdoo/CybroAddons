import { onWillDestroy, proxy, signal } from "@odoo/owl";
import { fuzzyLookup } from "@web/core/utils/search";
import { patch } from "@web/core/utils/patch";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { NavBar } from "@web/webclient/navbar/navbar";

const SIDEBAR_BODY_CLASS = "bb_sidebar_opened";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.sidebarState = proxy({
            isOpen: false,
            query: "",
            results: [],
        });
        this.searchInputRef = signal.ref();
        onWillDestroy(() => document.body.classList.remove(SIDEBAR_BODY_CLASS));
    },

    toggleSidebar() {
        this._setSidebarOpen(!this.sidebarState.isOpen);
    },

    _setSidebarOpen(isOpen) {
        this.sidebarState.isOpen = isOpen;
        document.body.classList.toggle(SIDEBAR_BODY_CLASS, isOpen);
        if (isOpen) {
            // Wait for the slide-in transition to make the input focusable
            setTimeout(() => this.searchInputRef()?.focus(), 50);
        } else {
            this._resetSidebarSearch();
        }
    },

    _resetSidebarSearch() {
        this.sidebarState.query = "";
        this.sidebarState.results = [];
        const input = this.searchInputRef();
        if (input) {
            input.value = "";
        }
    },

    onSidebarSearchInput(ev) {
        const query = ev.target.value.trim();
        this.sidebarState.query = query;
        this.sidebarState.results = query ? this._searchMenus(query) : [];
    },

    onSidebarSearchKeydown(ev) {
        if (ev.key === "Escape") {
            this._setSidebarOpen(false);
        } else if (ev.key === "Enter" && this.sidebarState.results.length) {
            this._openSidebarMenu(this.sidebarState.results[0].id);
        }
    },

    _searchMenus(query) {
        // Computed on demand so newly installed apps / reloaded menus are found
        const { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        const appResults = fuzzyLookup(query, apps, (menu) => menu.label);
        const menuResults = fuzzyLookup(query, menuItems, (menu) =>
            (menu.parents + " / " + menu.label).split("/").reverse().join("/")
        );
        return [...appResults, ...menuResults];
    },

    onSidebarMenuClick(ev, menuId) {
        // Keep the browser behaviour for "open in new tab"
        if (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button === 1) {
            return;
        }
        ev.preventDefault();
        this._openSidebarMenu(menuId);
    },

    _openSidebarMenu(menuId) {
        this._setSidebarOpen(false);
        this.menuService.selectMenu(menuId);
    },
});
