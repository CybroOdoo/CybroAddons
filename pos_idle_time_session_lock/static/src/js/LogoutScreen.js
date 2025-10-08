/**
 * @module pos_idle_time_session_lock.LogoutScreen
 * @description This module handles the session timer for the Point of Sale idle time session lock feature.
 */
odoo.define('pos_idle_time_session_lock.LogoutScreen', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
/**
     * Customized Chrome component with session timer functionality.
     *
     * @class LogoutScreen
     * @extends Chrome
     */
    class LogoutScreen extends PosComponent {
        /** Super the setup function */
        setup() {
            super.setup();
        }
        /** Calling the logout screen */
        async showLogoutScreen() {
            this.back();
        }
        /** Creating a back function when the screen is idle then it logout the screen */
        back() {
            this.props.resolve({ confirmed: false, payload: false });
            this.trigger('close-temp-screen');
            this.env.pos.hasLoggedIn = true;
            this.env.posbus.trigger('start-cash-control');
        }
        /** Returns the shop name */
        get shopName() {
            return this.env.pos.config.name;
        }
    }
    LogoutScreen.template = 'LogoutScreen';

    Registries.Component.add(LogoutScreen);

    return LogoutScreen;
});
