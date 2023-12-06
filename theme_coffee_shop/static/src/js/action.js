odoo.define("theme_coffee_shop.theme_coffee_shop_template", function (require) {
  "use strict";
    var publicWidget = require('web.public.widget');
    /** Public widget for login form **/
    publicWidget.registry.loginData = publicWidget.Widget.extend({
        selector: '.login-form-container',
        events:{
            'click .login-close': '_loginPageToggle',
        },
            /** Toggle the login page visibility **/
        _loginPageToggle: function(){
            this.el.classList.toggle('show');
            },
    });
    return publicWidget.registry.loginData;
});
