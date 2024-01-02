odoo.define('whatsapp_chat_layout.discuss_container', function(require) {
    'use strict';
    var rpc = require('web.rpc');
    const components = {
        Discuss: require('mail/static/src/components/discuss/discuss.js'),
    };
    const {
        patch
    } = require('web.utils');
    /**
    Patching the components.Discuss for changing the default view
    */
    patch(components.Discuss, 'discuss// model: "mail",ord-patch', {
        setup() {
             //Call rpc to get color value.
            rpc.query({
                model: "res.config.settings",
                method: "get_color",
                args: [0],
            }).then(function(result) {
                if (result.background_color !== false) {
                    document.documentElement.style.setProperty("--background-color", result.background_color);
                } //Set discuss background color
                if (result.layout_color !== false) {
                    document.documentElement.style.setProperty("--layout-color", result.layout_color);
                } // Set discuss layout color
                if (result.background_image !== false) {
                    document.documentElement.style.setProperty("--background-image", 'url(data:image/png;base64,' + result.background_image + ')');
                } // Set discuss background image
            });
        }
    });
})
