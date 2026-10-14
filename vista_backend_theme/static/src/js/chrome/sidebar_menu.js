import { Component, signal, useEffect } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";

const STORAGE_KEY = "vista_backend_theme.sidebar_open";

function readStoredState() {
    try {
        return browser.localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
        return false;
    }
}

/** Whether the app sidebar is opened; shared by the navbar toggle and the sidebar. */
export const sidebarOpen = signal(readStoredState());

export function toggleSidebar() {
    const isOpen = !sidebarOpen();
    sidebarOpen.set(isOpen);
    try {
        browser.localStorage.setItem(STORAGE_KEY, isOpen ? "1" : "0");
    } catch {
        // storage unavailable: the state just isn't remembered
    }
}

export class VistaSidebar extends Component {
    static template = "vista_backend_theme.Sidebar";

    setup() {
        this.menuService = useService("menu");
        // The layout (content shift) is driven by a class on the body
        useEffect(() => {
            document.body.classList.toggle("o_vista_sidebar_open", sidebarOpen());
            return () => document.body.classList.remove("o_vista_sidebar_open");
        });
    }

    get apps() {
        return this.menuService.getApps();
    }
    get currentAppId() {
        return this.menuService.getCurrentApp()?.id;
    }
    getIcon(app) {
        if (app.webIconData) {
            return { src: app.webIconData };
        }
        if (app.webIcon) {
            const [icon, color, background] = app.webIcon.split(",");
            return { icon, style: `color: ${color || "#fff"}; background-color: ${background || "transparent"};` };
        }
        return { src: "/web/static/img/default_icon_app.png" };
    }
    getHref(app) {
        return `/odoo/${app.actionPath || "action-" + app.actionID}`;
    }
    onAppClick(app) {
        this.menuService.selectMenu(app);
    }
}
registry.category("main_components").add("vista_backend_theme.Sidebar", {
    Component: VistaSidebar,
});

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.vistaSidebarOpen = sidebarOpen;
    },
    toggleVistaSidebar() {
        toggleSidebar();
    },
});
