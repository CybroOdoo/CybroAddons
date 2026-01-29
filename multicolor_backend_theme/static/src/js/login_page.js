odoo.define('multicolor_backend_theme.LoginPage', function (require) {
    "use strict";
    var rpc = require('web.rpc');

    var selected_theme = {};

    $(document).ready(function () {
        $.ajax({
            url: '/active_theme',
            type: 'get',
        }).then(function (result) {
            var colors = JSON.parse(result);
            $('.cybro-login-btn').css({
                'background-color': colors.theme_main_color,
                'color': colors.theme_font_color
            });
            $('.cybro-super-btn').css({
                'color': colors.view_font_color
            });
        });
    });
});