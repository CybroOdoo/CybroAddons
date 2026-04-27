/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useRef, useState, onWillStart } from "@odoo/owl";
import SearchResult from './SearchResult';
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { Deferred } from "@web/core/utils/concurrency";
/**
 * WebResponsive Component
 *
 * This component adds responsive search functionality within the Odoo web client.
 * It listens for key events and initiates a search when alphanumeric keys are pressed.
 * The search queries available applications and menu items and displays the matching results in a modal.
 */
class WebResponsive extends Component {
    /**
     * Initializes the component, sets up the state, services, and registers event listeners.
     */
    setup() {
        super.setup(...arguments);
        this.root = useRef('root');
        this.action = useService("action");
        this.menuService = useService('menu');
        this.state = useState({
            results: [],
            showModal: false,
            menus: [],
            should_replace_nav: false,
            query: "",
            selectedIndex: 0,
        });
        this._search_def = new Deferred();
        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        onWillStart(async () => {
            this.state.menus = await this.menuService.getApps();
            this.state.should_replace_nav = true;
        });
        this._boundKeyDown = this.onKeyDown.bind(this);
        window.addEventListener('keydown', this._boundKeyDown);
    }
    /**
     * Handles keydown events to trigger the search modal.
     *
     * @param {Event} event - The keydown event triggered by the user.
     */
     onKeyDown(event) {
        const isSearchInput = event.target.classList.contains("responsive_search_input");
        // Block Enter everywhere else
        if (event.key === "Enter" && !isSearchInput) {
            return;
        }
        const tag = event.target.tagName;
        const isTyping = tag === "INPUT" || tag === "TEXTAREA";
        // OPEN MODAL (only when closed)
        if (!this.state.showModal && !isTyping && /^[a-zA-Z0-9]$/.test(event.key)) {
            this.state.query = `${this.state.query}${event.key}`;
            this._searchMenus();
            this.state.showModal = true;
            setTimeout(() => {
                this.root.el?.querySelector(".responsive_search_input")?.focus();
            }, 100);
            return;
        }
        // AFTER MODAL OPEN → allow navigation even in input
        if (!this.state.showModal) return;
        // IMPORTANT: don't block arrows/enter anymore
        if (!this.state.results.length) return;
        if (event.key === "ArrowDown") {
            event.preventDefault();
            this.state.selectedIndex =
                (this.state.selectedIndex + 1) % this.state.results.length;
        }
        if (event.key === "ArrowUp") {
            event.preventDefault();
            this.state.selectedIndex =
                (this.state.selectedIndex - 1 + this.state.results.length) %
                this.state.results.length;
        }
        if (event.key === "Enter") {
            event.preventDefault();
            const selected = this.state.results[this.state.selectedIndex];
            if (selected) {
                this.onMenuClick(selected, { type: "click" });
            }
        }
    }
    /**
     * Closes the search modal, clears the search results and query.
     */
    closeModal() {
        this.state.showModal = false;
        this.state.results = [];
        this.state.query = "";
    }
    /**
     * Removes the keydown event listener when the component is unmounted.
     */
    willUnmount() {
        window.removeEventListener('keydown', this._boundKeyDown);
    }
    /**
     * Performs a search through the available apps and menu items using fuzzy matching.
     * Updates the search results in the component state.
     */
    _searchMenus() {
        var query = this.state.query;
        if (query === "") {
            return;
        }
        var results = [];
        // Search through apps
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
        // Search through menu items
        fuzzyLookup(query, this._searchableMenus, (menu) =>
                (menu.parents + " / " + menu.label).split("/").reverse().join("/"))
            .forEach((menu) => {
                results.push({
                    category: "menu_items",
                    name: menu.parents + " / " + menu.label,
                    actionID: menu.actionID,
                    id: menu.id,
                });
            });
        this.state.results = results.map((item, index) => ({
            ...item,
            _idx: index,
        }));
        this.state.selectedIndex = results.length ? 0 : -1;
    }
    /**
     * Handles the input event to update the search query and trigger a new search.
     *
     * @param {Event} event - The input event from the search field.
     */
    onInput(event) {
        this.state.query = event.target.value;
        this._searchMenus();
    }
     /**
     * Handles click event to open the action for selected menu.
     *
     * @param {Object} menu - The menu selected by the user.
     * @param {Event} ev - The click event triggered by the user.
     */
    async onMenuClick(menu, ev) {
        if (!ev || ev.type !== "click") {
            return;
        }
        if (menu.id) {
            await this.menuService.selectMenu(menu.id);
        }
        // 2. Execute action (actual view load)
        if (menu.actionID) {
            await this.action.doAction(menu.actionID);
        }
    }
}
WebResponsive.template = 'responsive_web.WebResponsiveTmp';
WebResponsive.components = {
    ...WebResponsive.components,
    SearchResult
};
registry.category('actions').add('web_responsive', WebResponsive);
