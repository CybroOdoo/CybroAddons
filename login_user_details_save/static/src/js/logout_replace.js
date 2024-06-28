odoo.define('login_user_details_save.login', function (require) {
    "use strict";

    const core = require('web.core');
    const { registry } = require('@web/core/registry');
    const { browser } = require('@web/core/browser/browser');
    // Ensure the correct registry categories are used
    const serviceRegistry = registry.category("services");
    const userMenuRegistry = registry.category("user_menuitems");
    // Define the service to remove the existing logout menu item
    const removeLogoutService = {
        start() {
            // Remove the existing log out menu item
           registry.category("user_menuitems").remove('log_out');
        },
    };
    // Add the service to the registry
    serviceRegistry.add("remove_log_out", removeLogoutService);
    // Define the new log out menu item
    function logOutItemNew(env) {
        const route = "/web/session/logout_popup";
        return {
            type: "item",
            id: "logout_new",
            class: "btn btn-link",
            description: env._t("Log out"),
            href: `${browser.location.origin}${route}`,
            callback: () => {
                browser.location.href = route;
            },
            sequence: 70,
        };
    }
    // Add the new log out menu item to the registry
    registry.category("user_menuitems").add("logout_new", logOutItemNew);
});
