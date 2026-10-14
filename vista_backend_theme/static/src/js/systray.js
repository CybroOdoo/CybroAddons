import { Component } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";

export const VISTA_THEMES = [
    { key: "blue", label: "Blue", color: "#386aeb" },
    { key: "black", label: "Black", color: "#1f2631" },
    { key: "green", label: "Green", color: "#00a97f" },
];

export class ThemeSwitcher extends Component {
    static template = "vista_backend_theme.ThemeSwitcher";
    static components = { Dropdown, DropdownItem };

    setup() {
        this.orm = useService("orm");
        this.themes = VISTA_THEMES;
    }

    async selectTheme(theme) {
        await this.orm.call("theme.data", "set_theme", [theme.key]);
        // Assets and app icons changed: reload to get the new bundles.
        browser.location.reload();
    }
}

registry.category("systray").add(
    "vista_backend_theme.theme_switcher",
    {
        Component: ThemeSwitcher,
        // The theme is shared by every user, only administrators can change it
        isDisplayed: () => user.isSystem,
    },
    { sequence: 22 }
);
