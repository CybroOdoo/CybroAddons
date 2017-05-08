odoo.define('change_password.UserMenu', function (require) {

var new_support = require('web.UserMenu');
var Model = require('web.DataModel');

new_support.include({

on_menu_new_password: function () {

        var new_password = prompt("Please enter your new password:", "Password");
        if (new_password){
            var Users = new Model('change.password');
            Users.call('change_password', [1, new_password]).then(function (result) {
                location.reload();
            });
        }
    },
});
});
