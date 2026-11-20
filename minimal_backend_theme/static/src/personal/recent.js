import { effect, onMounted, onWillDestroy } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { session } from "@web/session";

/**
 * What the user recently opened, most recent first, offered by the top bar
 * search when nothing is typed. Kept in the browser, per user and database:
 * a convenience only (names and access rights of records are checked again
 * on the server each time they are shown, menus against the user's menus).
 */
function createRecentList(name, { limit, isSame }) {
    const key = () => `minimal_backend_theme.${name}.${session.db}.${user.userId}`;
    const list = {
        read() {
            try {
                const items = JSON.parse(browser.localStorage.getItem(key()) || "[]");
                return Array.isArray(items) ? items : [];
            } catch {
                return [];
            }
        },
        write(items) {
            try {
                browser.localStorage.setItem(key(), JSON.stringify(items.slice(0, limit)));
            } catch {
                // Storage unavailable (private mode...): a convenience only.
            }
        },
        remember(item) {
            list.write([item, ...list.read().filter((other) => !isSame(other, item))]);
        },
        clear() {
            list.write([]);
        },
    };
    return list;
}

/** Menu ids. */
export const recentMenus = createRecentList("recent_menus", {
    limit: 6,
    isSame: (a, b) => a === b,
});

/** `{model, id}` of records opened in a form. */
export const recentRecords = createRecentList("recent_records", {
    limit: 12,
    isSame: (a, b) => a.model === b.model && a.id === b.id,
});

// Settings and other one-screen forms are not records worth listing.
const IGNORED_MODELS = ["res.config.settings"];

patch(FormController.prototype, {
    setup() {
        super.setup();
        // Main forms only (not dialogs), and saved records; also follows the
        // pager moving to another record (same pattern as the controller's
        // own action state tracking).
        if (this.env.inDialog || IGNORED_MODELS.includes(this.props.resModel)) {
            return;
        }
        let dispose = () => {};
        onMounted(() => {
            dispose = effect(() => {
                const resId = this.model.root?.resId;
                if (resId) {
                    recentRecords.remember({ model: this.props.resModel, id: resId });
                }
            });
        });
        onWillDestroy(() => dispose());
    },
});
