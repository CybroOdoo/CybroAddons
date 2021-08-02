odoo.define('code_backend_theme_enterprise.TopBar', function (require) {
"use strict";

/**
 * This file includes the UserMenu widget defined in Community to add or
 * override actions only available in Enterprise.
 */

var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var UserMenu = require('web.UserMenu');

var _t = core._t;
var QWeb = core.qweb;

UserMenu.include({
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    start: function () {
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    do_action() {
        return this._super(...arguments)
            .then(resp => {
                core.bus.trigger('close_o_burger_menu');
                return resp;
            });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _onMenuSupport: function () {
        window.open('https://www.odoo.com/help', '_blank');
    },
});





});