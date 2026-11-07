/** @odoo-module **/
import { expect, test } from "@odoo/hoot";
import { syncTogglesToSession } from "@backend_theme_infinito_plus/js/toggle_utils";

test("changed toggles are written to the session", () => {
    const session = { userEdit: false, sidebar: true, infinitoChameleon: false };
    syncTogglesToSession(session, {
        userEditToggler: true,
        sidebarToggler: false,
        chameleonToggler: true,
    });
    expect(session.userEdit).toBe(true);
    expect(session.sidebar).toBe(false);
    expect(session.infinitoChameleon).toBe(true);
});

test("toggles saved elsewhere are not written to the session", () => {
    const session = { infinitoDark: false, infinitoRefresh: false };
    syncTogglesToSession(session, { navbarDarkToggler: true, navbarRefreshToggler: true });
    expect(session.infinitoDark).toBe(false);
    expect(session.infinitoRefresh).toBe(false);
});

test("unknown toggles are ignored", () => {
    const session = {};
    syncTogglesToSession(session, { unknownToggler: true });
    expect(Object.keys(session).length).toBe(0);
});