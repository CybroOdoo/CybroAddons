odoo.define('restrict_web_debug.DebugMenuBasic', function (require) {
"use strict";
  const session = require('web.session');
  var DebugManager = require('web.DebugManager');
  /** Include DebugManager to disable option of debug **/
  DebugManager.include({
        start: function () {
            this._super.apply(this, arguments);
            if (session.user_group == false){
               this.$el.find('.o_debug_mode').addClass("d-none")
            }
        },
  });
});
