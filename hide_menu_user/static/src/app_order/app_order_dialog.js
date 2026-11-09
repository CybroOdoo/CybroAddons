import { Component, signal, t, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { useSortable } from "@web/core/utils/sortable_owl";

/**
 * Lets the user arrange their own apps. The order is saved in the user's
 * settings and applied server-side when the menus are loaded, so the navbar
 * apps menu and the Enterprise home screen follow it.
 */
export class AppOrderDialog extends Component {
    static template = "hide_menu_user.AppOrderDialog";
    static components = { Dialog };

    props = useProps({ close: t.function() });

    apps = signal([]);
    listRef = signal.ref();
    isBusy = signal(false);

    setup() {
        this.menuService = useService("menu");
        this.notification = useService("notification");
        this.apps.set(
            this.menuService.getApps().map((app) => ({
                id: app.id,
                name: app.name,
                iconSrc: app.webIconData || false,
            }))
        );
        useSortable({
            ref: this.listRef,
            elements: ".o_hide_menu_app_order_item",
            handle: ".o_hide_menu_app_order_handle",
            cursor: "grabbing",
            onDrop: (params) => this.onDrop(params),
        });
    }

    onDrop({ element, previous }) {
        const movedId = Number(element.dataset.appId);
        const previousId = previous ? Number(previous.dataset.appId) : null;
        const apps = this.apps().filter((app) => app.id !== movedId);
        const moved = this.apps().find((app) => app.id === movedId);
        const index = previousId === null ? 0 : apps.findIndex((app) => app.id === previousId) + 1;
        apps.splice(index, 0, moved);
        this.apps.set(apps);
    }

    move(index, offset) {
        const target = index + offset;
        const apps = [...this.apps()];
        if (target < 0 || target >= apps.length) {
            return;
        }
        [apps[index], apps[target]] = [apps[target], apps[index]];
        this.apps.set(apps);
    }

    async save() {
        await this.storeOrder(this.apps().map((app) => app.id));
        this.notification.add(_t("Your app order has been saved."), { type: "success" });
    }

    async resetToTeamOrder() {
        await this.storeOrder(false);
        this.notification.add(_t("Your apps now follow your team's order."), { type: "info" });
    }

    async storeOrder(order) {
        if (this.isBusy()) {
            return;
        }
        this.isBusy.set(true);
        try {
            await user.setUserSettings("hide_menu_app_order", order);
            // The server clears the Enterprise home screen order too: mirror
            // it locally so the home screen does not re-apply the old one.
            if ("homemenu_config" in user.settings) {
                user.updateUserSettings("homemenu_config", false);
            }
            await this.menuService.reload();
        } finally {
            this.isBusy.set(false);
        }
        this.props.close();
    }
}

function arrangeAppsItem() {
    const dialog = useService("dialog");
    return {
        type: "item",
        id: "hide_menu_user.arrange_apps",
        description: _t("Arrange My Apps"),
        callback: () => dialog.add(AppOrderDialog, {}),
        sequence: 55,
    };
}

registry.category("user_menuitems").add("hide_menu_user.arrange_apps", arrangeAppsItem);
