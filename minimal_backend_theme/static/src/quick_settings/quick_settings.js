import { Component, proxy, useProps, usePlugin } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";
import { ORM } from "@web/core/orm_plugin";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { localization } from "@web/core/l10n/localization";
import { useService } from "@web/core/utils/hooks";
import { MENU_SEARCH_SHORTCUT_LABEL } from "../menu_search/menu_index";
import { canEditOptions, getOption, saveOption } from "../theme_settings";

/** On/off options shown as switches (the menu layout has its own control). */
const LAYOUT_OPTIONS = [
    {
        key: "compact",
        label: _t("Compact view"),
        help: _t("Tighter rows and spacing"),
        icon: "menu",
    },
    {
        key: "full_width",
        label: _t("Full-width forms"),
        help: _t("Use the whole screen for forms"),
        icon: "expand_content",
    },
];

export class QuickSettings extends Component {
    static template = "minimal_backend_theme.QuickSettings";
    static components = { Dropdown, DropdownItem };
    props = useProps({});

    setup() {
        this.action = useService("action");
        this.menuSearch = useService("minimal_backend_theme.menu_search");
        this.orm = usePlugin(ORM);
        this.options = LAYOUT_OPTIONS;
        this.isSystem = user.isSystem;
        this.shortcutLabel = MENU_SEARCH_SHORTCUT_LABEL;
        this.notification = useService("notification");
        // The options are shared by all users (the Settings page shows the
        // same values): administrators change them, others see them.
        this.canEdit = canEditOptions();
        this.state = proxy({
            ...Object.fromEntries(LAYOUT_OPTIONS.map((o) => [o.key, getOption(o.key)])),
            menuLayout: getOption("menu_layout"),
            dark: getOption("dark_mode"),
            saving: false,
        });
        // The sidebar sits on the right in right-to-left languages.
        const sidebarIcon = localization.direction === "rtl" ? "dock_to_right" : "dock_to_left";
        this.menuLayouts = [
            { key: "horizontal", label: _t("Top bar"), icon: "toolbar" },
            { key: "vertical", label: _t("Sidebar"), icon: sidebarIcon },
        ];
    }

    get isDark() {
        return this.state.dark;
    }

    /**
     * Saves an option for everyone and updates this menu; on failure, puts
     * the switch back and tells why.
     */
    async save(stateKey, optionKey, value) {
        if (!this.canEdit || this.state.saving) {
            return;
        }
        const previous = this.state[stateKey];
        this.state[stateKey] = value;
        this.state.saving = true;
        try {
            await saveOption(optionKey, value);
        } catch (error) {
            this.state[stateKey] = previous;
            this.notification.add(_t("The option could not be saved."), { type: "danger" });
            throw error;
        } finally {
            this.state.saving = false;
        }
    }

    setMenuLayout(layout) {
        if (layout !== this.state.menuLayout) {
            return this.save("menuLayout", "menu_layout", layout);
        }
    }

    toggleOption(option) {
        return this.save(option.key, option.key, !this.state[option.key]);
    }

    /** Reloads the page once saved: the color scheme is chosen server side. */
    toggleDark() {
        return this.save("dark", "dark_mode", !this.state.dark);
    }

    async openPreferences() {
        const action = await this.orm.call("res.users", "action_get");
        action.res_id = user.userId;
        this.action.doAction(action);
    }

    /** General Settings, scrolled to the Backend Theme section. */
    async openSettings() {
        await this.action.doAction("base_setup.action_general_configuration");
        // The settings form renders after the action resolves.
        for (let i = 0; i < 20; i++) {
            const block = document.getElementById("minimal_backend_theme");
            if (block) {
                block.scrollIntoView({ block: "start" });
                return;
            }
            await new Promise((resolve) => setTimeout(resolve, 100));
        }
    }

    /** Switches listed at the top of the dropdown. */
    get switches() {
        return [
            {
                key: "dark",
                label: _t("Dark mode"),
                help: _t("Easier on the eyes at night"),
                icon: this.isDark ? "light_mode" : "dark_mode",
                checked: this.isDark,
                toggle: () => this.toggleDark(),
            },
            ...this.options.map((option) => ({
                key: option.key,
                label: option.label,
                help: option.help,
                icon: option.icon,
                checked: this.state[option.key],
                toggle: () => this.toggleOption(option),
            })),
        ];
    }
}

registry
    .category("systray")
    .add("minimal_backend_theme.quick_settings", { Component: QuickSettings }, { sequence: 2 });
