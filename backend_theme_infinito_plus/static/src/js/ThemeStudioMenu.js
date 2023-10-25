odoo.define('backend_theme_infinito_plus.ThemeStudioMenu', function (require) {
    "use strict";
    var ThemeStudioMenu = require('backend_theme_infinito.ThemeStudioMenu');
    var ajax = require('web.ajax');
    ThemeStudioMenu.include({
        //Reset all the features.
       _onResetClick: async function(ev){
            this._super.apply(this, arguments);
            await ajax.jsonRpc('/theme_studio_plus/reset_to_default_style', 'call', {});
        },
    })
});
