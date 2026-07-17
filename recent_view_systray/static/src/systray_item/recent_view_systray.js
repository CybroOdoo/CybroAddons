/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService, useBus } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { session } from "@web/session";
import { Component, useState, onWillStart } from "@odoo/owl";
import { router, routerBus } from "@web/core/browser/router";
import { browser } from "@web/core/browser/browser";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

const STORAGE_KEY = "recent_view_systray_items";

/**
 * RecentViewSystray Component
 * This component provides a systray icon that displays a dropdown
 * of recently visited views and records, allowing for quick navigation.
 */
export class RecentViewSystray extends Component {
    static template = "recent_view_systray.RecentViewSystray";
    static components = { Dropdown, DropdownItem };

    setup() {
        /**
         * Initialize services and state.
         * Subscribes to the UI updated bus to track navigation.
         */
        this.actionService = useService("action");
        this.menuService = useService("menu");
        this.orm = useService("orm");
        this.state = useState({
            recentViews: [],
        });

        onWillStart(() => {
            this.loadViews();
        });

        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", this.onUiUpdated);
    }

    get limit() {
        return user.context.history_limit || session.history_limit || 15;
    }

    get storageKey() {
        return `${STORAGE_KEY}_${user.userId}`;
    }

    async loadViews() {
        try {
            const stored = browser.localStorage.getItem(this.storageKey);
            if (stored) {
                const allMenus = this.menuService.getAll();
                const seenUrls = new Set();
                const seenNames = new Set();
                const actionIdsToFetch = [];
                
                const loadedViews = JSON.parse(stored).slice(0, this.limit);
                this.state.recentViews = loadedViews.map(item => {
                    if (item.actionId) {
                        const menu = allMenus.find(m => m.actionID == item.actionId);
                        if (menu) {
                            const parts = [menu.name];
                            let current = menu;
                            while (current.parent_id) {
                                const parent = this.menuService.getMenu(current.parent_id);
                                if (!parent || parent.id === "root" || !parent.name) break;
                                parts.unshift(parent.name);
                                current = parent;
                            }
                            let name = parts.join(" / ");
                            if (item.recordName) {
                                name += ` / ${item.recordName}`;
                            }
                            item.name = name;
                        } else {
                            actionIdsToFetch.push(item.actionId);
                        }
                    }
                    return item;
                }).filter(item => {
                    if (seenUrls.has(item.url) || seenNames.has(item.name)) return false;
                    seenUrls.add(item.url);
                    seenNames.add(item.name);
                    return true;
                });

                if (actionIdsToFetch.length > 0) {
                    await this.translateActions(actionIdsToFetch);
                }
            }
        } catch (e) {
            console.error("Failed to parse recent views", e);
        }
    }

    async translateActions(actionIds) {
        const uniqueIds = Array.from(new Set(actionIds.map(id => Number(id)).filter(id => !isNaN(id))));
        if (uniqueIds.length === 0) return;

        try {
            const actions = await this.orm.read("ir.actions.act_window", uniqueIds, ["name"]);
            const actionMap = Object.fromEntries(actions.map(a => [a.id, a.name]));

            this.state.recentViews = this.state.recentViews.map(item => {
                if (item.actionId && actionMap[item.actionId]) {
                    let name = actionMap[item.actionId];
                    if (item.recordName) {
                        name += ` / ${item.recordName}`;
                    }
                    return { ...item, name };
                }
                return item;
            });
        } catch (e) {
            console.error("Failed to translate actions via RPC", e);
        }
    }

    saveViews() {
        browser.localStorage.setItem(this.storageKey, JSON.stringify(this.state.recentViews));
    }

    onUiUpdated() {
        setTimeout(() => this.updateRecentViews(), 100);
    }

    updateRecentViews() {
        const controller = this.actionService.currentController;
        if (!controller || controller.action.tag === "menu" || !controller.displayName) {
            return;
        }

        let displayName = controller.displayName;
        let recordName = null;
        const breadcrumbItems = Array.from(document.querySelectorAll('.o_control_panel .breadcrumb-item'));
        
        if (breadcrumbItems.length > 0) {
            const breadcrumbTexts = breadcrumbItems.map(el => el.textContent.trim());
            displayName = breadcrumbTexts.join(" / ");
            
            // Detect if the last item is a record name (different from menu name)
            const menu = this.menuService.getAll().find(m => m.actionID == controller.action.id);
            if (menu && breadcrumbTexts.length > 0) {
                const lastItem = breadcrumbTexts[breadcrumbTexts.length - 1];
                if (lastItem !== menu.name) {
                    recordName = lastItem;
                }
            }
        } else {
            let title = document.title;
            if (title.endsWith(' - Odoo')) {
                title = title.substring(0, title.length - 7);
            }
            displayName = title;
        }

        const url = router.stateToUrl(router.current);
        const name = displayName;
        const actionId = controller.action.id;

        if (!name || name === "Odoo") {
            return;
        }

        const newEntry = { name, url, actionId, recordName };

        let filteredViews = this.state.recentViews.filter(v => {
            if (v.url === url) return false;
            if (v.name === name) return false;
            if (actionId && v.actionId && v.actionId == actionId && !recordName && !v.recordName) return false;
            return true;
        });
        filteredViews.unshift(newEntry);

        if (filteredViews.length > this.limit) {
            filteredViews = filteredViews.slice(0, this.limit);
        }

        this.state.recentViews = filteredViews;
        this.saveViews();
    }

    /**
     * Handles the click event on a recent view item.
     * Parses the stored URL and updates the router state to perform navigation.
     * This method uses the router and routerBus to ensure that the WebClient
     * synchronizes both the Action Manager and the Menu Service (header).
     * @param {Object} view The recent view item object containing the URL.
     */
    onRecentViewClick(view) {
        const url = new URL(view.url, browser.location.origin);
        const state = router.urlToState(url);
        if (state) {
            // Update router state synchronously
            router.pushState(state, { sync: true });
            routerBus.trigger("ROUTE_CHANGE");
        }
    }
}

export const systrayItem = {
    Component: RecentViewSystray,
};

registry.category("systray").add("recent_view_systray", systrayItem, { sequence: 30 });
