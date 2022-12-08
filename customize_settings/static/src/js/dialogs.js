odoo.define('customize_settings.dialog', async function(require){
    "use strict";
    const { Dialog } = require("@web/core/dialog/dialog");
    const { patch } = require("@web/core/utils/patch");
    patch(Dialog.prototype,"customize_settings.Dialog",{
    setup() {
        this._super(...arguments);
        console.log(this.props)
        this.props.title = 'System'
    }
    });
});

