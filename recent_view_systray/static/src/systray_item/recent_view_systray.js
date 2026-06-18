/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService, useBus } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { session } from "@web/session";
import { Component, useState, onWillStart } from "@odoo/owl";
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
        /**
         * Loads stored recent views from localStorage and translates all action
         * names using the server (ORM) to respect the current UI language.
         */
        try {
            const stored = browser.localStorage.getItem(this.storageKey);
            if (stored) {
                const seenUrls = new Set();
                const loadedViews = JSON.parse(stored).slice(0, this.limit);

                // Collect all numeric action IDs to fetch translated names
                const actionIdsToFetch = [];
                this.state.recentViews = loadedViews.filter(item => {
                    if (seenUrls.has(item.url)) return false;
                    seenUrls.add(item.url);
                    return true;
                });

                for (const item of this.state.recentViews) {
                    const numId = Number(item.actionId);
                    if (item.actionId && !isNaN(numId)) {
                        actionIdsToFetch.push(numId);
                    }
                }

                if (actionIdsToFetch.length > 0) {
                    await this.translateActions(actionIdsToFetch);
                }
            }
        } catch (e) {
            console.error("Failed to parse recent views", e);
        }
    }

    async translateActions(actionIds) {
        /**
         * Fetches action names from the server and reconstructs display names
         * using the current language context for action names (leaf) and
         * parent path (from menuService).
         */
        const uniqueIds = Array.from(new Set(actionIds.map(id => Number(id)).filter(id => !isNaN(id))));
        if (uniqueIds.length === 0) return;

        try {
            const allMenus = this.menuService.getAll();
            const actions = await this.orm.read("ir.actions.actions", uniqueIds, ["name"]);
            const actionMap = Object.fromEntries(actions.map(a => [a.id, a.name]));
            const isEnglish = (user.context.lang || session.user_context?.lang || "en").startsWith("en");
            const hasNonAscii = (str) => /[^\x00-\x7F]/.test(str);

            this.state.recentViews = this.state.recentViews.map(item => {
                const numId = Number(item.actionId);
                if (!item.actionId || isNaN(numId) || !actionMap[numId]) {
                    return item;
                }

                const actionName = actionMap[numId];
                const menu = allMenus.find(m => m.actionID == numId);
                
                // Smart heuristic to pick the best translated leaf name
                let leaf = actionName;
                if (menu) {
                    if (isEnglish) {
                        // If session is English, but actionName is English and menu.name is Arabic,
                        // prefer actionName. If both are Arabic, we're stuck, but usually actionName is better.
                        if (hasNonAscii(menu.name) && !hasNonAscii(actionName)) {
                            leaf = actionName;
                        } else {
                            leaf = menu.name;
                        }
                    } else {
                        // If session is non-English (e.g. Arabic), and actionName is English
                        // but menu.name is translated (Arabic), prefer the menu name.
                        if (!hasNonAscii(actionName) && hasNonAscii(menu.name)) {
                            leaf = menu.name;
                        } else {
                            leaf = actionName;
                        }
                    }
                }

                let name;
                if (menu) {
                    const parts = [leaf];
                    let current = menu;
                    while (current.parent_id) {
                        const parent = this.menuService.getMenu(current.parent_id);
                        if (!parent || parent.id === "root" || !parent.name) break;
                        
                        let parentName = parent.name;
                        // Apply same heuristic to parent names if possible
                        if (isEnglish && hasNonAscii(parentName)) {
                            // We don't have an actionId for parents easily here, 
                            // but we can try to find if it has an English name in the menu service? 
                            // Odoo menu service usually only has one name.
                        }

                        parts.unshift(parentName);
                        current = parent;
                    }
                    name = parts.join(" / ");
                } else {
                    name = leaf;
                }

                if (item.recordName) {
                    name += ` / ${item.recordName}`;
                }
                return { ...item, name };
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

        // Build URL from current browser location (hash-based routing)
        const url = browser.location.pathname + browser.location.search + browser.location.hash;
        const name = displayName;
        const actionId = controller.action.id;

        if (!name || name === "Odoo") {
            return;
        }

        const newEntry = { name, url, actionId, recordName };

        let filteredViews = this.state.recentViews.filter(v => {
            if (actionId && v.actionId && v.actionId == actionId) return false;
            // Also check URL to be safe
            if (v.url === url) return false;
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
     * Navigate to a stored recent view URL.
     * In Odoo 18, DropdownItem calls ev.preventDefault() then onSelected(),
     * so we must provide onSelected to actually perform navigation.
     * @param {string} url - The URL to navigate to.
     */
    navigateToUrl(url) {
        browser.location.href = url;
    }
}

export const systrayItem = {
    Component: RecentViewSystray,
};

registry.category("systray").add("recent_view_systray", systrayItem, { sequence: 30 });
