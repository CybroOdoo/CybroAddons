odoo.define('multicolor_backend_theme.LoginPage', function(require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    // change the theme of login page according to the active backend theme
    publicWidget.registry.LoginPage = publicWidget.Widget.extend({
        selector: '.oe_login_buttons',
        start: function() {
            $.ajax({
                url: '/active_theme',
                type: 'get',
            }).then(function(result) {
                var colors = JSON.parse(result);
                $('.cybro-login-btn').css({
                    'background-color': colors.theme_main_color,
                    'color': colors.theme_font_color
                });
                $('.cybro-super-btn').css({
                    'color': colors.view_font_color
                });
            });
            return this._super(...arguments);
        },
    });
    return publicWidget.registry.LoginPage;
});
