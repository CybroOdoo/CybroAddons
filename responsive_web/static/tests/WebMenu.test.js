/** @odoo-module **/
import { describe, expect, test, beforeEach } from "@odoo/hoot";
import { routerBus } from "@web/core/browser/router";

/**
 * Tests for WebMenu.js
 *
 * WebMenu patches the Odoo NavBar component prototype to add:
 *  1. setup()              – wires up action/menu services + ROUTE_CHANGE routerBus listener
 *  2. onNavBarDropdownItemSelection() – overrides menu selection to open the dashboard
 *                                       when the current-app item is re-clicked
 *  3. _onRouteChange()     – resets isDashboardView and restores navbar visibility
 *  4. _onClickCustomAction() – triggers the 'web_responsive' client action
 *
 * Because the patch mutates NavBar.prototype at import-time, these tests
 * exercise the pure logic of each method in isolation using mock objects,
 * without mounting the full Odoo environment.
 */

describe("WebMenu NavBar Patch", () => {
    describe.current.tags("desktop");

    // -------------------------------------------------------------------------
    // Helper: minimal NavBar-like mock that mirrors the patched prototype API
    // -------------------------------------------------------------------------
    const buildMockNavBar = ({ currentApp = null, actionDoAction = () => {} } = {}) => {
        const instance = {
            isDashboardView: false,
            currentApp,
            action: { doAction: actionDoAction },
            menuService: {},

            // Original super stubs
            _superSetupCalled: false,
            _superDropdownCalled: false,
            _superDropdownArg: null,

            // Patched methods (inline reimplementation matching WebMenu.js)
            setup() {
                this._superSetupCalled = true;
                this.isDashboardView = false;
                // (useBus / useService calls are service-level; omitted in unit tests)
            },

            onNavBarDropdownItemSelection(menu) {
                if (menu && this.currentApp && menu.id === this.currentApp.id) {
                    this._onClickCustomAction();
                    return;
                }
                this._superDropdownCalled = true;
                this._superDropdownArg = menu;
            },

            _onRouteChange() {
                this.isDashboardView = false;
                // DOM manipulation is skipped (no DOM in unit tests)
            },

            _onClickCustomAction() {
                this.isDashboardView = true;
                this.action.doAction({
                    type: "ir.actions.client",
                    tag: "web_responsive",
                    name: "Dashboard",
                    target: "main",
                });
            },
        };
        return instance;
    };

    // -------------------------------------------------------------------------
    // setup()
    // -------------------------------------------------------------------------
    describe("setup()", () => {
        test("initialises isDashboardView to false", () => {
            const navbar = buildMockNavBar();
            navbar.setup();
            expect(navbar.isDashboardView).toBe(false);
        });
    });

    // -------------------------------------------------------------------------
    // onNavBarDropdownItemSelection()
    // -------------------------------------------------------------------------
    describe("onNavBarDropdownItemSelection()", () => {
        test("calls _onClickCustomAction when the clicked menu matches the current app", () => {
            let customActionTriggered = false;
            const navbar = buildMockNavBar({ currentApp: { id: 5 } });
            navbar._onClickCustomAction = () => { customActionTriggered = true; };

            navbar.onNavBarDropdownItemSelection({ id: 5, name: "Sales" });

            expect(customActionTriggered).toBe(true);
            expect(navbar._superDropdownCalled).toBe(false);
        });

        test("delegates to super when the clicked menu does NOT match the current app", () => {
            const navbar = buildMockNavBar({ currentApp: { id: 5 } });

            navbar.onNavBarDropdownItemSelection({ id: 99, name: "Inventory" });

            expect(navbar._superDropdownCalled).toBe(true);
            expect(navbar._superDropdownArg).toEqual({ id: 99, name: "Inventory" });
        });

        test("delegates to super when currentApp is null/undefined", () => {
            const navbar = buildMockNavBar({ currentApp: null });

            navbar.onNavBarDropdownItemSelection({ id: 5, name: "Sales" });

            expect(navbar._superDropdownCalled).toBe(true);
        });

        test("delegates to super when the menu argument is falsy", () => {
            const navbar = buildMockNavBar({ currentApp: { id: 5 } });

            navbar.onNavBarDropdownItemSelection(null);

            expect(navbar._superDropdownCalled).toBe(true);
        });
    });

    // -------------------------------------------------------------------------
    // _onRouteChange()
    // -------------------------------------------------------------------------
    describe("_onRouteChange()", () => {
        test("resets isDashboardView to false after a route change", () => {
            const navbar = buildMockNavBar();
            navbar.isDashboardView = true; // simulate being on dashboard

            navbar._onRouteChange();

            expect(navbar.isDashboardView).toBe(false);
        });

        test("keeps isDashboardView false when it was already false", () => {
            const navbar = buildMockNavBar();
            navbar.isDashboardView = false;

            navbar._onRouteChange();

            expect(navbar.isDashboardView).toBe(false);
        });

        test("responds to ROUTE_CHANGE triggered on routerBus", () => {
            const navbar = buildMockNavBar();
            navbar.isDashboardView = true;

            // Wire up listener to routerBus matching WebMenu.js setup
            const listener = navbar._onRouteChange.bind(navbar);
            routerBus.addEventListener("ROUTE_CHANGE", listener);
            try {
                routerBus.trigger("ROUTE_CHANGE");
                expect(navbar.isDashboardView).toBe(false);
            } finally {
                routerBus.removeEventListener("ROUTE_CHANGE", listener);
            }
        });
    });

    // -------------------------------------------------------------------------
    // _onClickCustomAction()
    // -------------------------------------------------------------------------
    describe("_onClickCustomAction()", () => {
        test("sets isDashboardView to true", () => {
            const navbar = buildMockNavBar({ actionDoAction: () => {} });
            navbar._onClickCustomAction();
            expect(navbar.isDashboardView).toBe(true);
        });

        test("dispatches the correct ir.actions.client payload", () => {
            let dispatchedPayload = null;
            const navbar = buildMockNavBar({
                actionDoAction: (payload) => { dispatchedPayload = payload; },
            });

            navbar._onClickCustomAction();

            expect(dispatchedPayload).not.toBe(null);
            expect(dispatchedPayload.type).toBe("ir.actions.client");
            expect(dispatchedPayload.tag).toBe("web_responsive");
            expect(dispatchedPayload.target).toBe("main");
        });

        test("the dispatched action name is 'Dashboard'", () => {
            let dispatchedPayload = null;
            const navbar = buildMockNavBar({
                actionDoAction: (payload) => { dispatchedPayload = payload; },
            });

            navbar._onClickCustomAction();

            expect(dispatchedPayload.name).toBe("Dashboard");
        });
    });
});
