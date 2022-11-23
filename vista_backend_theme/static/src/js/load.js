odoo.define('vista_backend_theme.Load', function (require) {
    "use strict";

    var rpc = require('web.rpc');
    var session = require('web.session');

    $(document).ready(function () {
        rpc.query({
            model: 'theme.data',
            method: 'action_apply',
            args: [this]
        });
    });
});