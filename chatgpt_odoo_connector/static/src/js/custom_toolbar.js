odoo.define('chatgpt_odoo_connector.custom_toolbar', function (require) {
    'use strict';
    var web_editor = require('web_editor.toolbar');
    var Dialog = require('web.Dialog');
    var AlternativeChatGPT = require('chatgpt_odoo_connector.alternative_chatgpt');
    /* Adding a new button to the toolbar */
    var toolbar = web_editor.include({
        start: function () {
            var res = this._super.apply(this, arguments);
            this.$el.on('click', '#open-chatgpt', this._onButtonClick.bind(this));
            return res;
        },
        /* Function for showing the widget while clicking the button. */
        _onButtonClick: function () {
            if (!this.alternativeChatGPT || this.alternativeChatGPT.isDestroyed()) {
                this.alternativeChatGPT = new AlternativeChatGPT(this);
            }
            this.alternativeChatGPT.appendTo(this.el.offsetParent);
        },
    });
});
