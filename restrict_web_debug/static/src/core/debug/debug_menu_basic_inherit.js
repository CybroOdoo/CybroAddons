/** @odoo-module **/

import { DebugMenuBasic } from "@web/core/debug/debug_menu_basic";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

patch(DebugMenuBasic.prototype, {
//    Setup method to super the already existing features of this class and add extra features
    setup() {
        super.setup();
        this.user_debug = session.user_group[0]
    },
});
