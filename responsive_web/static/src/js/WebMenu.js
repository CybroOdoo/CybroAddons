/** @odoo-module **/
import { useService, useBus } from "@web/core/utils/hooks";
import { useRef } from "@odoo/owl";
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
/**
 * Patch for the NavBar Component
 *
 * This patch modifies the setup and behavior of the existing NavBar component within the Odoo web client.
 * It introduces custom actions, including detecting route changes and conditionally displaying the main navbar.
 */
patch(NavBar.prototype, {
    /**
     * Sets up the component by initializing services, state variables, and registering a bus listener
     * for route changes. This method is called when the component is initialized.
     */
    setup() {
        super.setup(...arguments);
        this.root = useRef('root');
        this.action = useService("action");
        this.menuService = useService("menu");
        this.isDashboardView = false;
        useBus(this.env.bus, 'ROUTE_CHANGE', this._onRouteChange.bind(this));
    },
    /**
     * Handles route changes by resetting the dashboard view flag and ensuring the main navbar is displayed.
     *
     * This method is called whenever a route change event is detected.
     */
    _onRouteChange() {
        this.isDashboardView = false;
        const mainNavbar = this.root.el.querySelector('.o_main_navbar');
        if (mainNavbar) {
            mainNavbar.style.display = '';
        }
    },
    /**
     * Custom action handler for when a specific action is triggered, such as switching to a dashboard view.
     * This method sets the dashboard view flag, triggers a client action, and handles the visibility of
     * the main navbar.
     */
    _onClickCustomAction() {
        this.isDashboardView = true;
        // Trigger a client action to load the 'Web Responsive' dashboard
        this.action.doAction({
            type: 'ir.actions.client',
            tag: 'web_responsive',
            name: 'Web Responsive',
            name: _t('Dashboard'),
            target: 'main'
        });
        const mainNavbar = this.root.el.querySelector('.o_main_navbar');
        const systray = this.root.el.querySelector('o_menu_systray');
        if (mainNavbar && this.isDashboardView) {
        }
    }
});
