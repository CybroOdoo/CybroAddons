odoo.define('pos_timesheet.PosHeaderLockButton', function(require) {
    'use strict';
    const HeaderLockButton = require('point_of_sale.HeaderLockButton');
    const Registries = require('point_of_sale.Registries');
    /** Extends HeaderLockButton to super showLoginScreen function */
    const PosHeaderLockButton = HeaderLockButton =>
        class extends HeaderLockButton {
        async showLoginScreen() {
            await this.env.pos._handleTimesheet(this.env.pos.get('cashier'))
            super.showLoginScreen()
        }
    };
    Registries.Component.extend(HeaderLockButton, PosHeaderLockButton);
    return HeaderLockButton;
});
