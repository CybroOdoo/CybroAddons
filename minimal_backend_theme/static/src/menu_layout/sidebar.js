import { Component, proxy, useListener, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { render } from "@web/owl2/utils";
import { WebClient } from "@web/webclient/webclient";

/**
 * Left sidebar listing the current app's menus, used when the menu layout
 * is "vertical" (Quick settings > Menu layout). It is always rendered and
 * only shown by CSS while <body> has the menu layout class, so switching the
 * layout is instant and needs no re-render of the web client.
 */
// Collapsed or expanded, remembered per browser (a pure UI preference).
const COLLAPSED_KEY = "minimal_backend_theme.sidebar_collapsed";
// Below this width (tablets), the expanded sidebar would squeeze the page:
// it rests as the slim rail and opens over the content, as a drawer.
// Matches Bootstrap's xl breakpoint (see theme.scss).
const DRAWER_MEDIA = "(max-width: 1199.98px)";

function readCollapsed() {
    try {
        return browser.localStorage.getItem(COLLAPSED_KEY) === "1";
    } catch {
        return false;
    }
}

export class MinimalSidebar extends Component {
    static template = "minimal_backend_theme.Sidebar";
    props = useProps({});

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.pins = useService("minimal_backend_theme.pins");
        useListener(this.pins.bus, "PINS-CHANGED", () => render(this));
        // Groups the user folded, by menu id (all groups start unfolded).
        // The page content follows the sidebar's width (see theme.scss).
        const drawerMedia = window.matchMedia(DRAWER_MEDIA);
        this.state = proxy({
            folded: {},
            collapsed: readCollapsed(),
            isDrawer: drawerMedia.matches,
            drawerOpen: false,
        });
        useListener(drawerMedia, "change", (ev) => {
            this.state.isDrawer = ev.matches;
            this.state.drawerOpen = false;
        });
        // Escape closes the open drawer. Caught on the document before the
        // hotkey service sees it: the drawer is on top of the page, so its
        // Escape comes first (the hotkey service would hand it to the most
        // recent registration, e.g. the search bar of the page underneath).
        useListener(
            document,
            "keydown",
            (ev) => {
                if (ev.key === "Escape" && this.state.drawerOpen) {
                    ev.stopPropagation();
                    ev.preventDefault();
                    this.state.drawerOpen = false;
                }
            },
            { capture: true }
        );
        // The menus service and the action manager are not reactive: re-render
        // when the app changes or another action is displayed (active entry).
        useListener(this.env.bus, "MENUS:APP-CHANGED", () => render(this));
        useListener(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => {
            this.syncActiveAction();
            render(this);
        });
        this.activeActionId = null;
        this.syncActiveAction();
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    get sections() {
        const app = this.currentApp;
        return app ? this.menuService.getMenuAsTree(app.id).childrenTree : [];
    }

    /**
     * Highlights the menu whose action is displayed. When the user moves on
     * to an action no menu opens (a button, a smart button...), the menu
     * they came from stays highlighted.
     */
    syncActiveAction() {
        const actionId = this.actionService.currentController?.action?.id;
        if (actionId && this.menuService.getAll().some((m) => m.actionID === actionId)) {
            this.activeActionId = actionId;
        }
    }

    isActive(menu) {
        return Boolean(menu.actionID) && menu.actionID === this.activeActionId;
    }

    hasActiveChild(menu) {
        return menu.childrenTree.some((child) =>
            child.childrenTree.length ? this.hasActiveChild(child) : this.isActive(child)
        );
    }

    isFolded(menu) {
        // A group holding the current page never hides it.
        return Boolean(this.state.folded[menu.id]) && !this.hasActiveChild(menu);
    }

    toggleGroup(menu) {
        this.state.folded[menu.id] = !this.isFolded(menu);
    }

    /** Pinned menus, from any app, that the user can still open. */
    get pinnedMenus() {
        return this.pins.ids
            .map((id) => this.menuService.getMenu(id))
            .filter((menu) => menu && menu.actionID);
    }

    /** Image of the app a menu belongs to, if it has one. */
    appIconOf(menu) {
        return this.menuService.getMenu(menu.appID)?.webIconData || false;
    }

    isPinned(menu) {
        return this.pins.isPinned(menu.id);
    }

    pinLabel(menu) {
        return this.isPinned(menu) ? _t("Unpin") : _t("Pin to the top");
    }

    togglePin(ev, menu) {
        ev.preventDefault();
        ev.stopPropagation();
        return this.pins.toggle(menu.id);
    }

    /**
     * Shown as the slim rail: on wide screens, as the user left it; on
     * tablets, unless the drawer is open.
     */
    get isCollapsed() {
        return this.state.isDrawer ? !this.state.drawerOpen : this.state.collapsed;
    }

    get toggleLabel() {
        return this.isCollapsed ? _t("Expand sidebar") : _t("Collapse sidebar");
    }

    /** Collapses the sidebar to a slim rail (app icon only), or expands it. */
    toggleCollapsed() {
        if (this.state.isDrawer) {
            this.state.drawerOpen = !this.state.drawerOpen;
            return;
        }
        const collapsed = !this.state.collapsed;
        this.state.collapsed = collapsed;
        try {
            browser.localStorage.setItem(COLLAPSED_KEY, collapsed ? "1" : "0");
        } catch {
            // Storage unavailable: the choice still applies for this page.
        }
    }

    href(menu) {
        return `/odoo/${menu.actionPath || "action-" + menu.actionID}`;
    }

    onMenuClick(ev, menu) {
        if (ev.ctrlKey || ev.metaKey) {
            return; // let the browser open the link in a new tab
        }
        ev.preventDefault();
        this.state.drawerOpen = false;
        this.menuService.selectMenu(menu);
    }
}

// Rendered by the web.WebClient template extension in sidebar.xml.
WebClient.components = { ...WebClient.components, MinimalSidebar };

function registerOnEnterprise(module) {
    if (module?.WebClientEnterprise) {
        module.WebClientEnterprise.components = {
            ...module.WebClientEnterprise.components,
            MinimalSidebar,
        };
    }
}

registerOnEnterprise(odoo.loader?.modules?.get("@web_enterprise/webclient/webclient"));
odoo.loader?.bus?.addEventListener("module-started", (ev) => {
    if (ev.detail?.moduleName === "@web_enterprise/webclient/webclient") {
        registerOnEnterprise(ev.detail.module);
    }
});
