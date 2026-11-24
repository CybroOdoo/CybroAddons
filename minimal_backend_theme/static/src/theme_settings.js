import { EventBus } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { cookie } from "@web/core/browser/cookie";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

/**
 * Theme display options: one set of values shared by all users, stored on
 * the server. Settings > General Settings > Backend Theme and the Quick
 * settings menu of the top bar both edit them (administrators only; other
 * users see them read-only). They reach the web client in the session info
 * (see models/ir_http.py).
 */
const settings = {
    menu_layout: "horizontal",
    dark_mode: false,
    compact: false,
    full_width: false,
    can_edit: false,
    ...session.minimal_backend_theme,
};

/**
 * Notified with {key, value} whenever an option changes, for components
 * whose rendering depends on one (e.g. the chatter position in full-width
 * forms, see full_width_forms/full_width_forms.js).
 */
export const themeBus = new EventBus();

/** Options applied as a class on <body>, with how a value maps to it. */
const BODY_OPTIONS = {
    menu_layout: { className: "o_minimal_menu_vertical", isOn: (v) => v === "vertical" },
    compact: { className: "o_minimal_compact", isOn: (v) => Boolean(v) },
    full_width: { className: "o_minimal_full_width", isOn: (v) => Boolean(v) },
};

/** Whether the current user may change the options (administrators). */
export function canEditOptions() {
    return Boolean(settings.can_edit);
}

export function getOption(key) {
    return settings[key];
}

function applyOption(key, value) {
    settings[key] = value;
    const option = BODY_OPTIONS[key];
    if (option) {
        document.body.classList.toggle(option.className, option.isOn(value));
    }
    themeBus.trigger("OPTION-CHANGED", { key, value });
}

/**
 * Saves an option for everyone - the value the Settings page shows - and
 * applies it to this page. Layout options apply at once (and are put back if
 * saving fails); the dark mode reloads the page, as the color scheme is a
 * different CSS bundle chosen server side.
 */
export async function saveOption(key, value) {
    const previous = settings[key];
    if (key !== "dark_mode") {
        applyOption(key, value);
    }
    try {
        await rpc("/web/dataset/call_kw/res.config.settings/minimal_theme_set_option", {
            model: "res.config.settings",
            method: "minimal_theme_set_option",
            args: [key, value],
            kwargs: {},
        });
    } catch (error) {
        if (key !== "dark_mode") {
            applyOption(key, previous);
        }
        throw error;
    }
    if (key === "dark_mode") {
        browser.location.reload();
    }
}

// Apply the options before the web client's first paint.
registry.category("services").add("minimal_backend_theme.theme_settings", {
    start() {
        for (const key of Object.keys(BODY_OPTIONS)) {
            applyOption(key, settings[key]);
        }
        // Core reads this cookie to style its own widgets (graphs, code
        // editor, PDF viewer) for the color scheme in use.
        cookie.set("color_scheme", settings.dark_mode ? "dark" : "light");
    },
});
