import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { proxy, onWillStart } from "@odoo/owl";
import { user } from "@web/core/user";
import { _t } from "@web/core/l10n/translation";

const COLOR_FIELDS = ["theme_main_color", "theme_font_color", "view_font_color"];

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.themeState = proxy({ themes: [], selected: null, isManager: false });
        this.themeOrm = useService("orm");
        this.themeNotification = useService("notification");
        onWillStart(async () => {
            const [isManager, themes] = await Promise.all([
                user.hasGroup("multicolor_backend_theme.multicolor_theme_manager_access"),
                this.themeOrm.searchRead("theme.config", [], ["name", "is_theme_active", ...COLOR_FIELDS]),
            ]);
            this.themeState.isManager = isManager;
            this.themeState.themes = themes;
            this.themeState.selected = themes.find((theme) => theme.is_theme_active) || themes[0] || null;
            this.applyThemeColors();
        });
    },

    applyThemeColors() {
        const theme = this.themeState.selected;
        if (theme) {
            for (const field of COLOR_FIELDS) {
                document.documentElement.style.setProperty(`--${field}`, theme[field]);
            }
        }
    },

    onChangeTheme(ev) {
        this.themeState.selected = this.themeState.themes.find((theme) => theme.id === Number(ev.target.value));
    },

    themeColorValue(field) {
        const color = this.themeState.selected[field] || "#000000";
        return /^#[0-9a-f]{3}$/i.test(color)
            ? "#" + [...color.slice(1)].map((digit) => digit + digit).join("")
            : color;
    },

    async onChangeThemeColor(ev, field) {
        const theme = this.themeState.selected;
        const color = ev.target.value;
        await this.themeOrm.write("theme.config", [theme.id], { [field]: color });
        theme[field] = color;
        if (theme.is_theme_active) {
            this.applyThemeColors();
        }
    },

    async onClickApply() {
        const theme = this.themeState.selected;
        if (!theme) {
            return;
        }
        await this.themeOrm.call("theme.config", "update_active_theme", [theme.id]);
        for (const record of this.themeState.themes) {
            record.is_theme_active = record.id === theme.id;
        }
        this.applyThemeColors();
        this.themeNotification.add(_t("Theme has been successfully updated"), { type: "success" });
    },

    async onClickCreate() {
        const [theme] = await this.themeOrm.call("theme.config", "create_new_theme", []);
        this.themeState.themes.push(theme);
        this.themeState.selected = this.themeState.themes.find((record) => record.id === theme.id);
    },

    async onClickRemove() {
        const theme = this.themeState.selected;
        if (theme.is_theme_active) {
            this.themeNotification.add(_t("You cannot delete an active theme."), { type: "warning" });
            return;
        }
        await this.themeOrm.unlink("theme.config", [theme.id]);
        this.themeState.themes = this.themeState.themes.filter((record) => record.id !== theme.id);
        this.themeState.selected = this.themeState.themes.find((record) => record.is_theme_active)
            || this.themeState.themes[0] || null;
    },

    async onThemeNameChange(ev) {
        const theme = this.themeState.selected;
        const name = ev.target.value.trim() || theme.name;
        await this.themeOrm.write("theme.config", [theme.id], { name });
        theme.name = name;
    },
});
