import { Component, computed, onWillStart, signal } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { fuzzyLookup } from "@web/core/utils/search";

const MAX_SEARCH_RESULTS = 20;

/**
 * Navbar entry listing the menus starred by the user and the team shortcuts
 * of their menu profile. Menus are resolved through the menu service, so a
 * menu the user can no longer see is never displayed.
 */
export class FavoriteMenu extends Component {
    static template = "hide_menu_user.FavoriteMenu";
    static components = { Dropdown, DropdownItem };

    personalIds = signal([]);
    sharedIds = signal([]);
    searchTerm = signal("");
    currentMenuId = signal(null);

    setup() {
        this.orm = useService("orm");
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.dropdown = useDropdownState();
        this.labels = {
            add: _t("Add to favourites"),
            remove: _t("Remove from favourites"),
            pinned: _t("Shared by your administrator"),
        };

        onWillStart(() => this.loadFavorites());
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.detectCurrentMenu());
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.detectCurrentMenu());
    }

    /** Personal favourites grouped by app, in the order they were starred. */
    personalGroups = computed(() => {
        const groups = new Map();
        for (const entry of this.resolveMenus(this.personalIds())) {
            if (!groups.has(entry.appId)) {
                groups.set(entry.appId, { appId: entry.appId, appName: entry.appName, entries: [] });
            }
            groups.get(entry.appId).entries.push(entry);
        }
        return [...groups.values()];
    });

    /** Parent menu of every menu, to build the "App / Menu / Sub-menu" path. */
    parentById = computed(() => {
        const parents = new Map();
        for (const menu of this.menuService.getAll()) {
            for (const childId of menu.children || []) {
                parents.set(childId, menu);
            }
        }
        return parents;
    });

    sharedEntries = computed(() => this.resolveMenus(this.sharedIds()));

    /** Every menu with an action matching the search, starred or not. */
    searchResults = computed(() => {
        const term = this.searchTerm().trim();
        if (!term) {
            return [];
        }
        const candidates = this.menuService
            .getAll()
            .filter((menu) => menu.id && menu.actionID)
            .map((menu) => this.toEntry(menu));
        return fuzzyLookup(term, candidates, (entry) => `${entry.fullPath} ${entry.name}`).slice(
            0,
            MAX_SEARCH_RESULTS
        );
    });

    currentEntry = computed(() => {
        const menu = this.currentMenuId() && this.menuService.getMenu(this.currentMenuId());
        return menu ? this.toEntry(menu) : null;
    });

    async loadFavorites() {
        const { personal, shared } = await this.orm.call(
            "hide.menu.favorite",
            "get_starred_menu_ids",
            []
        );
        this.personalIds.set(personal);
        this.sharedIds.set(shared);
    }

    /**
     * Find the menu matching the action currently displayed. An app's root
     * menu borrows the action of its first sub-menu, so a real sub-menu is
     * preferred, then one that belongs to the current app.
     */
    detectCurrentMenu() {
        const actionId = this.actionService.currentController?.action?.id;
        if (!actionId) {
            this.currentMenuId.set(null);
            return;
        }
        const currentAppId = this.menuService.getCurrentApp()?.id;
        const matches = this.menuService
            .getAll()
            .filter((menu) => menu.actionID === actionId)
            .sort((a, b) => (a.id === a.appID) - (b.id === b.appID));
        const menu = matches.find((m) => m.appID === currentAppId) || matches[0];
        this.currentMenuId.set(menu ? menu.id : null);
    }

    resolveMenus(menuIds) {
        return menuIds
            .map((menuId) => this.menuService.getMenu(menuId))
            .filter((menu) => menu && menu.actionID)
            .map((menu) => this.toEntry(menu));
    }

    toEntry(menu) {
        const app = this.menuService.getMenu(menu.appID);
        const parents = [];
        let node = this.parentById().get(menu.id);
        while (node && node.id && node.id !== menu.appID) {
            parents.unshift(node.name);
            node = this.parentById().get(node.id);
        }
        const appName = app ? app.name : "";
        return {
            id: menu.id,
            menu,
            appId: menu.appID,
            appName,
            name: menu.name,
            parentPath: parents.join(" / "),
            fullPath: [appName, ...parents].filter(Boolean).join(" / "),
        };
    }

    isFavorite(menuId) {
        return this.personalIds().includes(menuId);
    }

    isShared(menuId) {
        return this.sharedIds().includes(menuId);
    }

    onOpened() {
        this.detectCurrentMenu();
        this.loadFavorites();
    }

    onSearchInput(ev) {
        this.searchTerm.set(ev.target.value);
    }

    async openEntry(entry) {
        this.searchTerm.set("");
        await this.menuService.selectMenu(entry.menu);
    }

    async toggleFavorite(menuId) {
        const isFavorite = await this.orm.call("hide.menu.favorite", "toggle_star", [
            menuId,
        ]);
        const ids = this.personalIds().filter((id) => id !== menuId);
        this.personalIds.set(isFavorite ? [...ids, menuId] : ids);
        if (isFavorite) {
            this.sharedIds.set(this.sharedIds().filter((id) => id !== menuId));
        }
    }
}

registry
    .category("systray")
    .add("hide_menu_user.favorite_menu", { Component: FavoriteMenu }, { sequence: 25 });
