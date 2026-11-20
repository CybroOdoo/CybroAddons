import { Component, proxy, signal, t, useProps, usePlugin } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { isMacOS } from "@web/core/browser/feature_detection";
import { Dialog } from "@web/core/dialog/dialog";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { _t } from "@web/core/l10n/translation";
import { ORM } from "@web/core/orm_plugin";
import { registry } from "@web/core/registry";
import { KeepLast } from "@web/core/utils/concurrency";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { recentMenus, recentRecords } from "../personal/recent";
import {
    MENU_SEARCH_HOTKEY,
    MENU_SEARCH_SHORTCUT_LABEL,
    appIcon,
    buildMenuIndex,
    highlightChunks,
    menuHref,
    normalize,
    searchMenus,
} from "./menu_index";

// Shown at once, the menus list stays short enough for the records (listed
// after them) to remain in view.
const MENU_RESULT_LIMIT = 8;
const MENU_RESULT_LIMIT_WITH_RECORDS = 5;
const MENU_SCOPE_LIMIT = 50;
// Lookalike menus (no menu contains the query) come after the records.
const SIMILAR_MENU_LIMIT = 3;
const RECORD_MIN_QUERY_LENGTH = 2;
const RECORD_SEARCH_DELAY = 250;
const RECENT_RECORD_LIMIT = 6;
const CREATE_RESULT_LIMIT = 8;

// What can be created ("new ..."): the same for the whole session, fetched
// once on first use.
let createTargetsPromise = null;

export class MenuSearchDialog extends Component {
    static template = "minimal_backend_theme.MenuSearchDialog";
    static components = { Dialog };
    props = useProps({
        close: t.function(),
    });

    inputRef = signal.ref();
    listRef = signal.ref();

    setup() {
        this.menuService = useService("menu");
        this.isMacOS = isMacOS();
        this.index = buildMenuIndex(this.menuService);
        this.byId = new Map(this.index.map((e) => [e.id, e]));
        this.actionService = useService("action");
        this.orm = usePlugin(ORM);
        this.state = proxy({
            query: "",
            activeIndex: 0,
            recentIds: recentMenus.read(),
            recordGroups: [],
            recordsLoading: false,
            scope: "all",
            pinnedIds: [],
            recentRecords: [],
            createTargets: [],
        });
        this.pins = useService("minimal_backend_theme.pins");
        this.state.pinnedIds = [...this.pins.ids];
        this.loadPersonalLists();
        this.scopes = [
            { key: "all", label: _t("All") },
            { key: "menus", label: _t("Menus") },
            { key: "records", label: _t("Records") },
        ];
        this.apps = this.menuService.getApps();
        this.keepLast = new KeepLast();
        this.searchRecordsDebounced = useDebounced(() => this.searchRecords(), RECORD_SEARCH_DELAY);

        useAutofocus({ ref: this.inputRef });
        const opts = { bypassEditableProtection: true, allowRepeat: true };
        useHotkey("arrowdown", () => this.move(1), opts);
        useHotkey("arrowup", () => this.move(-1), opts);
        useHotkey("enter", () => this.openActive(false), { bypassEditableProtection: true });
        useHotkey("control+enter", () => this.openActive(true), {
            bypassEditableProtection: true,
        });
        useHotkey("tab", () => this.cycleScope(1), { bypassEditableProtection: true });
        useHotkey("shift+tab", () => this.cycleScope(-1), { bypassEditableProtection: true });
    }

    get recent() {
        return this.state.recentIds.map((id) => this.byId.get(id)).filter(Boolean);
    }

    /**
     * What the dialog lists, as sections of selectable items; every item
     * carries its position in the keyboard navigation order (`index`).
     *   - no query: recently opened menus
     *   - query: matching menus, then matching records grouped by model,
     *     restricted to the chosen scope (All / Menus / Records)
     * Also returns the number of matches per scope, shown on the tabs.
     */
    get view() {
        const sections = [];
        const items = [];
        const add = (section, item) => {
            item.index = items.length;
            items.push(item);
            section.items.push(item);
        };
        if (!this.hasQuery) {
            const pinned = this.pinned;
            const pinnedSection = { key: "pinned", title: _t("Pinned"), items: [] };
            for (const entry of pinned) {
                add(pinnedSection, { key: `pin_${entry.id}`, kind: "menu", entry });
            }
            const recordSection = { key: "recent_records", title: _t("Recent records"), items: [] };
            for (const recent of this.state.recentRecords) {
                const group = { model: recent.model, label: recent.label, menu_id: recent.menu_id };
                add(recordSection, {
                    key: `recent_${recent.model}_${recent.id}`,
                    kind: "record",
                    group,
                    record: recent,
                    app: this.byId.get(recent.menu_id)?.app,
                    showType: true,
                });
            }
            const pinnedIds = new Set(pinned.map((entry) => entry.id));
            const menuSection = { key: "recent", title: _t("Recent menus"), items: [] };
            for (const entry of this.recent.filter((entry) => !pinnedIds.has(entry.id))) {
                add(menuSection, { key: `menu_${entry.id}`, kind: "menu", entry });
            }
            for (const section of [pinnedSection, recordSection, menuSection]) {
                if (section.items.length) {
                    sections.push(section);
                }
            }
            return { sections, items, counts: {} };
        }
        const scope = this.state.scope;
        const menus = searchMenus(this.index, this.state.query);
        const groups = this.state.recordGroups;
        const recordCount = groups.reduce((sum, group) => sum + group.records.length, 0);
        const counts = {
            menus: menus.length,
            records: recordCount,
            recordsMore: groups.some((group) => group.has_more),
        };
        counts.all = counts.menus + counts.records;
        counts.recordsLoading = this.state.recordsLoading && this.canSearchRecords;

        const showMenus = scope !== "records";
        const showRecords = scope !== "menus";

        const createTargets = scope === "all" ? this.matchCreateTargets(this.state.query) : [];
        if (createTargets.length) {
            const section = { key: "create", title: _t("Create"), items: [] };
            for (const target of createTargets) {
                add(section, {
                    key: `create_${target.model}`,
                    kind: "create",
                    target,
                    entry: this.byId.get(target.menu_id),
                });
            }
            sections.push(section);
        }
        const hasRecords = showRecords && groups.length > 0;
        const menuSection = (title, limit) => {
            const section = { key: "menus", title, count: menus.length, items: [] };
            for (const entry of menus.slice(0, limit)) {
                add(section, { key: `menu_${entry.id}`, kind: "menu", entry });
            }
            sections.push(section);
        };
        if (showMenus && menus.length && !menus.fuzzy) {
            let limit = hasRecords ? MENU_RESULT_LIMIT_WITH_RECORDS : MENU_RESULT_LIMIT;
            if (scope === "menus") {
                limit = MENU_SCOPE_LIMIT;
            }
            menuSection(_t("Menus"), limit);
        }
        if (showRecords && this.showRecordPlaceholders) {
            // Keeps the records' place while they load, so the list does
            // not jump when they arrive.
            sections.push({ key: "records_loading", title: _t("Records"), items: [] });
        }
        if (showRecords) {
            for (const group of groups) {
                const appEntry = this.byId.get(group.menu_id);
                const section = {
                    key: `model_${group.model}`,
                    title: group.label,
                    count: group.records.length,
                    countMore: group.has_more,
                    group,
                    items: [],
                };
                for (const record of group.records) {
                    add(section, {
                        key: `record_${group.model}_${record.id}`,
                        kind: "record",
                        group,
                        record,
                        app: appEntry?.app,
                    });
                }
                if (group.has_more) {
                    add(section, { key: `more_${group.model}`, kind: "more", group });
                }
                sections.push(section);
            }
        }
        if (showMenus && menus.length && menus.fuzzy) {
            const recordsExpected = hasRecords || (showRecords && counts.recordsLoading);
            let limit = recordsExpected ? SIMILAR_MENU_LIMIT : MENU_RESULT_LIMIT;
            if (scope === "menus") {
                limit = MENU_SCOPE_LIMIT;
            }
            menuSection(_t("Similar menus"), limit);
        }
        return { sections, items, counts };
    }

    /** Records are on their way: placeholder rows instead of an empty list. */
    get showRecordPlaceholders() {
        return (
            this.state.scope !== "menus" &&
            this.state.recordsLoading &&
            this.canSearchRecords &&
            !this.state.recordGroups.length
        );
    }

    get pinned() {
        return this.state.pinnedIds.map((id) => this.byId.get(id)).filter(Boolean);
    }

    isPinned(entry) {
        return this.state.pinnedIds.includes(entry.id);
    }

    pinLabel(entry) {
        return this.isPinned(entry) ? _t("Unpin") : _t("Pin to the top");
    }

    async togglePin(ev, entry) {
        ev.preventDefault();
        ev.stopPropagation();
        this.state.pinnedIds = [...(await this.pins.toggle(entry.id))];
    }

    /** Recent records and what can be created, fetched without blocking. */
    async loadPersonalLists() {
        const recent = recentRecords.read();
        if (recent.length) {
            this.orm
                .call("minimal_backend_theme.global_search", "get_recent_records", [recent], {
                    limit: RECENT_RECORD_LIMIT,
                })
                .then((records) => (this.state.recentRecords = records));
        }
        createTargetsPromise ||= this.orm.call(
            "minimal_backend_theme.global_search",
            "get_create_targets",
            []
        );
        try {
            this.state.createTargets = await createTargetsPromise;
        } catch {
            createTargetsPromise = null; // retried on the next opening
        }
    }

    /**
     * "new lead", "create invoice"...: the record types the rest of the
     * query names (by type, app or menu), or all of them for a bare "new".
     */
    matchCreateTargets(query) {
        const words = normalize(query).trim().split(/\s+/).filter(Boolean);
        const keywords = new Set(["new", "create", normalize(_t("new")), normalize(_t("create"))]);
        if (!words.length || !keywords.has(words[0])) {
            return [];
        }
        const rest = words.slice(1);
        return this.state.createTargets
            .filter((target) => {
                const entry = this.byId.get(target.menu_id);
                if (!entry) {
                    return false;
                }
                const haystack = normalize(`${target.label} ${entry.haystack}`);
                return rest.every((word) => haystack.includes(word));
            })
            .slice(0, CREATE_RESULT_LIMIT);
    }

    setScope(scope) {
        this.state.scope = scope;
        this.state.activeIndex = 0;
        this.inputRef()?.focus();
    }

    cycleScope(delta) {
        const keys = this.scopes.map((scope) => scope.key);
        const next = (keys.indexOf(this.state.scope) + delta + keys.length) % keys.length;
        this.setScope(keys[next]);
    }

    clearQuery() {
        this.state.query = "";
        this.state.activeIndex = 0;
        this.state.recordGroups = [];
        this.state.recordsLoading = false;
        this.keepLast.add(Promise.resolve());
        const input = this.inputRef();
        if (input) {
            input.value = "";
            input.focus();
        }
    }

    // Whole sentences with placeholders, so that translators can reorder
    // them (and right-to-left languages lay them out properly).

    createLabel(target) {
        return _t("New %(type)s", { type: target.label });
    }

    seeAllLabel(group) {
        return _t("See all %(type)s matching “%(query)s”", {
            type: group.label,
            query: this.state.query.trim(),
        });
    }

    get noResultsLabel() {
        return _t("No results for “%(query)s”", { query: this.state.query.trim() });
    }

    /** Short label of an item for the "open" hint of the selected row. */
    actionLabel(item) {
        if (item.kind === "create") {
            return _t("Create");
        }
        return item.kind === "more" ? _t("Show") : _t("Open");
    }

    get items() {
        return this.view.items;
    }

    get canSearchRecords() {
        return this.state.query.trim().length >= RECORD_MIN_QUERY_LENGTH;
    }

    get hasQuery() {
        return Boolean(this.state.query.trim());
    }

    get shortcutLabel() {
        return MENU_SEARCH_SHORTCUT_LABEL;
    }

    href(item) {
        if (item.kind === "menu") {
            return menuHref(item.entry.menu);
        }
        if (item.kind === "record") {
            const { model } = item.group;
            const menu = this.byId.get(item.group.menu_id)?.menu;
            const base = menu
                ? `/odoo/${menu.actionPath || "action-" + menu.actionID}`
                : `/odoo/${model.includes(".") ? model : "m-" + model}`;
            return `${base}/${item.record.id}`;
        }
        if (item.kind === "create" && item.entry) {
            return `${menuHref(item.entry.menu)}/new`;
        }
        return null;
    }

    iconOf(app) {
        return appIcon(app);
    }

    highlight(label) {
        return highlightChunks(label, this.state.query);
    }

    onInput(ev) {
        this.state.query = ev.target.value;
        this.state.activeIndex = 0;
        if (this.canSearchRecords) {
            this.state.recordsLoading = true;
            this.searchRecordsDebounced();
        } else {
            this.keepLast.add(Promise.resolve());
            this.state.recordGroups = [];
            this.state.recordsLoading = false;
        }
    }

    /** Fetches the records matching the query (latest query wins). */
    async searchRecords() {
        const query = this.state.query.trim();
        if (query.length < RECORD_MIN_QUERY_LENGTH) {
            return;
        }
        try {
            const groups = await this.keepLast.add(
                this.orm.call("minimal_backend_theme.global_search", "search_records", [query])
            );
            this.state.recordGroups = groups;
        } finally {
            if (this.state.query.trim() === query) {
                this.state.recordsLoading = false;
            }
        }
        this.state.activeIndex = Math.min(this.state.activeIndex, Math.max(this.items.length - 1, 0));
    }

    move(delta) {
        const count = this.items.length;
        if (!count) {
            return;
        }
        this.state.activeIndex = (this.state.activeIndex + delta + count) % count;
        const el = this.listRef()?.querySelector(
            `[data-index="${this.state.activeIndex}"]`
        );
        el?.scrollIntoView({ block: "nearest" });
    }

    openActive(newTab) {
        const item = this.items[this.state.activeIndex];
        if (item) {
            this.open(item, newTab);
        }
    }

    onResultClick(ev, item) {
        const newTab = (ev.ctrlKey || ev.metaKey) && item.kind !== "more";
        if (!newTab) {
            ev.preventDefault();
        }
        this.open(item, newTab);
    }

    open(item, newTab = false) {
        if (newTab) {
            if (item.kind === "menu") {
                recentMenus.remember(item.entry.id);
            }
            const href = this.href(item);
            if (href) {
                browser.open(href, "_blank");
            }
            return;
        }
        this.props.close();
        if (item.kind === "menu") {
            recentMenus.remember(item.entry.id);
            this.menuService.selectMenu(item.entry.menu);
        } else if (item.kind === "record") {
            this.openRecord(item.group, item.record.id);
        } else if (item.kind === "create") {
            this.openCreate(item.entry);
        } else {
            this.openAllRecords(item.group);
        }
    }

    /** Opens a record in the app that manages its model when there is one. */
    openRecord(group, resId) {
        const model = group.model;
        const entry = this.byId.get(group.menu_id);
        if (entry) {
            return this.actionService.doAction(entry.menu.actionID, {
                clearBreadcrumbs: true,
                viewType: "form",
                props: { resId },
                onActionReady: () => this.menuService.setCurrentMenu(entry.menu),
            });
        }
        return this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                res_model: model,
                res_id: resId,
                views: [[false, "form"]],
                target: "current",
            },
            { clearBreadcrumbs: true }
        );
    }

    /** A new record, in the app whose menu opens that record type. */
    openCreate(entry) {
        return this.actionService.doAction(entry.menu.actionID, {
            clearBreadcrumbs: true,
            viewType: "form",
            onActionReady: () => this.menuService.setCurrentMenu(entry.menu),
        });
    }

    /** "See all": every matching record of a model, in a list. */
    openAllRecords(group) {
        const entry = this.byId.get(group.menu_id);
        return this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                name: group.label,
                res_model: group.model,
                domain: [["display_name", "ilike", this.state.query.trim()]],
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
            },
            {
                clearBreadcrumbs: true,
                onActionReady: () => entry && this.menuService.setCurrentMenu(entry.app),
            }
        );
    }

    openApp(ev, app) {
        if (ev.ctrlKey || ev.metaKey) {
            return; // let the browser open the link in a new tab
        }
        ev.preventDefault();
        this.props.close();
        this.menuService.selectMenu(app);
    }

    clearRecent() {
        recentMenus.clear();
        this.state.recentIds = [];
    }
}

/**
 * Opens the menu search dialog; a single instance at a time.
 */
export const menuSearchService = {
    dependencies: ["dialog", "hotkey"],
    start(env, { dialog, hotkey }) {
        let closeDialog = null;
        const open = () => {
            if (closeDialog) {
                return;
            }
            closeDialog = dialog.add(
                MenuSearchDialog,
                {},
                {
                    onClose: () => {
                        closeDialog = null;
                    },
                }
            );
        };
        hotkey.add(MENU_SEARCH_HOTKEY, open, { bypassEditableProtection: true, global: true });
        return { open };
    },
};
registry.category("services").add("minimal_backend_theme.menu_search", menuSearchService);

/**
 * Search field in the top bar: opens the menu search dialog.
 */
export class MenuSearchSystray extends Component {
    static template = "minimal_backend_theme.MenuSearchSystray";
    props = useProps({});

    setup() {
        this.menuSearch = useService("minimal_backend_theme.menu_search");
        this.shortcutLabel = MENU_SEARCH_SHORTCUT_LABEL;
        this.placeholder = _t("Search menus and records...");
    }
}
registry
    .category("systray")
    .add("minimal_backend_theme.menu_search", { Component: MenuSearchSystray }, { sequence: 1100 });
