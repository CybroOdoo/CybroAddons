odoo.define('restrict_web_debug.debug_menu', function (require) {
"use strict";
    const { onMounted } = owl.hooks;
    const { DebugMenuBasic } = require("@web/core/debug/debug_menu_basic");
    const { patch } = require('web.utils');
    const { useRef } = owl.hooks;
    const session = require('web.session');
     /** Patch DebugMenuBasic to disable option of debug **/
    patch(DebugMenuBasic.prototype, "restrict_web_debug", {
        setup() {
            this._super(...arguments);
            this.root = useRef("DebugDropDown");
            onMounted(() => {
                 if (session.user_group == false) {
                    $(this.root.el).addClass("d-none")
                }
            });
        }
    })
});
