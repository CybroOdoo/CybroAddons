odoo.define('restrict_web_debug.debug_menu', function (require) {
"use strict";
//    const { useEnvDebugContext } = require("@/web/core//debug_context");
    const { Dropdown } = require ("@web/core/dropdown/dropdown");
    console.log(Dropdown, 'dropppp')
    const { DropdownItem } = require("@web/core/dropdown/dropdown_item");
    const { Component } = require("@odoo/owl");
    const {DebugMenuBasic} = require("@web/core/debug/debug_menu_basic");
    const { patch } = require('web.utils');
    const session = require('web.session');

    console.log(DebugMenuBasic, 'console1111111111')

    patch(DebugMenuBasic.prototype, "test_patching_my_component", {
        setup() {
            this._super();
            this.user_debug = session.user_group
            console.log('ooo', this.user_debug)
        }

    })



});
//DebugMenuBasic.components = {
//    Dropdown,
//    DropdownItem,
//};
//DebugMenuBasic.template = "web.DebugMenu";



///** @odoo-module **/
//

//

//    });
