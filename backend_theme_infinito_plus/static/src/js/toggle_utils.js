/** @odoo-module **/

// Checkboxes whose value is saved by the base _SaveChanges (element id -> session key)
export const SYNCED_TOGGLES = {
    userEditToggler: "userEdit",
    sidebarToggler: "sidebar",
    sidebarIconToggler: "sidebarIcon",
    sidebarNameToggler: "sidebarName",
    navbarHoverToggler: "fullscreen",
    sidebarCompanyToggler: "sidebarCompany",
    sidebarUserToggler: "sidebarUser",
    navbarRecentToggler: "recentApps",
    navbarFullScreenAppToggler: "fullScreenApp",
    navbarMenuBookmarkToggler: "infinitoBookmark",
    chameleonToggler: "infinitoChameleon",
    navbarRTLToggler: "infinitoRtl",
};

// Checkboxes saved elsewhere: dark mode has its own handler, Refresh is saved by the Plus controller
export const OTHER_TOGGLES = {
    navbarDarkToggler: "infinitoDark",
    navbarRefreshToggler: "infinitoRefresh",
};

/**
 * Writes the toggles the user changed into the session object.
 * @param {Object} session - the session info object.
 * @param {Object} changedToggles - element id -> checked.
 */
export function syncTogglesToSession(session, changedToggles) {
    for (const [id, checked] of Object.entries(changedToggles)) {
        const key = SYNCED_TOGGLES[id];
        if (key) {
            session[key] = checked;
        }
    }
}