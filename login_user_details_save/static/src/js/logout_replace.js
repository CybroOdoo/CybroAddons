/** @odoo-module **/
import {registry} from "@web/core/registry";
import {browser} from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";


const serviceRegistry = registry.category("services");
const userMenuRegistry = registry.category("user_menuitems");
const removeLogoutService = {
    start() {
        userMenuRegistry.remove('log_out');
    },
};
serviceRegistry.add("remove_log_out", removeLogoutService);

function logOutItemNew(env) {
    const route = "/web/session/logout_popup";
    return {
        type: "item",
        id: "logout_new",
        class: "btn btn-link",
        description: _t("Log out"),
        href: `${browser.location.origin}${route}`,
        callback: () => {
            browser.location.href = route;
        },
        sequence: 70,
    };
}

registry.category("user_menuitems").add("logout", logOutItemNew)
