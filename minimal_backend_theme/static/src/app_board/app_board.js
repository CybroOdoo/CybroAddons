import { Component, proxy, signal, t, useListener, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { localization } from "@web/core/l10n/localization";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useActiveElement } from "@web/core/ui/ui_plugin";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { appIcon, buildMenuIndex, highlightChunks, menuHref, searchMenus } from "../menu_search/menu_index";
import { recentMenus } from "../personal/recent";

const MENU_RESULT_LIMIT = 8;

/**
 * Full-screen app board: every app as a large tile, with a search field that
 * filters the apps and also lists matching menus of any app.
 */
export class AppBoardPanel extends Component {
    static template = "minimal_backend_theme.AppBoardPanel";
    props = useProps({ close: t.function() });

    root = signal.ref();
    inputRef = signal.ref();

    setup() {
        this.menuService = useService("menu");
        this.apps = this.menuService.getApps();
        this.index = buildMenuIndex(this.menuService);
        this.byId = new Map(this.index.map((entry) => [entry.id, entry]));
        // Pinned menus (star in the search and the sidebar): shortcuts
        // above the apps while nothing is typed.
        this.pins = useService("minimal_backend_theme.pins");
        this.state = proxy({ query: "", activeIndex: 0 });

        // Hotkeys of the page underneath stay inactive while the board is open.
        useActiveElement(this.root);
        useAutofocus({ ref: this.inputRef });
        // The board's keys are caught on the document before Odoo's hotkey
        // service sees them. Through the service, the newest registration
        // wins: a view still loading underneath when the board opens would
        // register its own Escape and arrows afterwards and take them over.
        // The board covers the whole screen and owns the keyboard while open.
        // Left/right follow the reading direction: in right-to-left
        // languages the next tile is on the left.
        const forward = localization.direction === "rtl" ? -1 : 1;
        const actions = {
            Escape: () => this.props.close(),
            ArrowRight: () => this.move(forward, true),
            ArrowLeft: () => this.move(-forward, true),
            ArrowDown: () => this.move(1, false),
            ArrowUp: () => this.move(-1, false),
            Enter: (ev) => this.openActive(ev.ctrlKey || ev.metaKey),
        };
        useListener(
            document,
            "keydown",
            (ev) => {
                const action = actions[ev.key];
                if (!action || ev.isComposing || ev.altKey || ev.shiftKey) {
                    return;
                }
                ev.preventDefault();
                ev.stopPropagation();
                action(ev);
            },
            { capture: true }
        );
    }

    get hasQuery() {
        return Boolean(this.state.query.trim());
    }

    get pinned() {
        return this.pins.ids.map((id) => this.byId.get(id)).filter(Boolean);
    }

    clearQuery() {
        this.state.query = "";
        this.state.activeIndex = 0;
        const input = this.inputRef();
        if (input) {
            input.value = "";
            input.focus();
        }
    }

    get filteredApps() {
        if (!this.hasQuery) {
            return this.apps;
        }
        const words = this.state.query.toLowerCase().trim().split(/\s+/);
        return this.apps.filter((app) => words.every((w) => app.name.toLowerCase().includes(w)));
    }

    get menuResults() {
        if (!this.hasQuery) {
            return [];
        }
        // Apps already listed above are not repeated as menus.
        const appIds = new Set(this.filteredApps.map((app) => app.id));
        return searchMenus(this.index, this.state.query)
            .filter((entry) => !appIds.has(entry.id))
            .slice(0, MENU_RESULT_LIMIT);
    }

    /** Apps then menus, in display order, for keyboard navigation. */
    get items() {
        return [
            ...this.filteredApps.map((app) => ({ menu: app, isApp: true })),
            ...this.menuResults.map((entry) => ({ menu: entry.menu, isApp: false })),
        ];
    }

    get noResultsLabel() {
        return _t("Nothing matches “%(query)s”", { query: this.state.query.trim() });
    }

    iconOf(app) {
        return appIcon(app);
    }

    highlight(label) {
        return highlightChunks(label, this.state.query);
    }

    href(menu) {
        return menuHref(menu);
    }

    /** Number of tiles in the first row of the app grid, as laid out by CSS. */
    get gridColumns() {
        const tiles = [...(this.root()?.querySelectorAll(".o_minimal_app_board_grid > *") || [])];
        if (!tiles.length) {
            return 1;
        }
        const firstTop = tiles[0].offsetTop;
        return tiles.filter((tile) => tile.offsetTop === firstTop).length;
    }

    /**
     * Moves the keyboard selection. Horizontal moves step one item; vertical
     * moves jump a row in the app grid, and one line in the menu list.
     */
    move(delta, horizontal) {
        const items = this.items;
        if (!items.length) {
            return;
        }
        const appCount = this.filteredApps.length;
        const current = this.state.activeIndex;
        let next = current + delta;
        if (!horizontal && current < appCount) {
            const cols = this.gridColumns;
            next = current + delta * cols;
            if (delta > 0 && next >= appCount) {
                // Leaving the grid downwards: last row, or first menu.
                const lastRowStart = appCount - (appCount % cols || cols);
                next = current >= lastRowStart ? appCount : appCount - 1;
            }
        }
        next = Math.max(0, Math.min(items.length - 1, next));
        this.state.activeIndex = next;
        this.root()
            ?.querySelector(`[data-board-index="${next}"]`)
            ?.scrollIntoView({ block: "nearest" });
    }

    onInput(ev) {
        this.state.query = ev.target.value;
        this.state.activeIndex = 0;
    }

    openActive(newTab) {
        const item = this.items[this.state.activeIndex];
        if (item) {
            this.open(item.menu, newTab);
        }
    }

    onItemClick(ev, menu) {
        const newTab = ev.ctrlKey || ev.metaKey;
        if (!newTab) {
            ev.preventDefault();
        }
        this.open(menu, newTab);
    }

    open(menu, newTab = false) {
        recentMenus.remember(menu.id);
        if (newTab) {
            browser.open(this.href(menu), "_blank");
            return;
        }
        this.props.close();
        this.menuService.selectMenu(menu);
    }
}

/** Mounts the panel while the board is open (main component, always there). */
export class AppBoard extends Component {
    static template = "minimal_backend_theme.AppBoard";
    static components = { AppBoardPanel };
    props = useProps({});

    setup() {
        this.board = useService("minimal_backend_theme.app_board");
    }
}

export const appBoardService = {
    start() {
        const state = proxy({ isOpen: false });
        return {
            state,
            open() {
                state.isOpen = true;
            },
            close() {
                state.isOpen = false;
            },
            toggle() {
                state.isOpen = !state.isOpen;
            },
        };
    },
};

registry.category("services").add("minimal_backend_theme.app_board", appBoardService);
registry.category("main_components").add("minimal_backend_theme.AppBoard", { Component: AppBoard });

// The top bar's apps button opens the board (see app_board.xml).
patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.appBoard = useService("minimal_backend_theme.app_board");
    },
});
