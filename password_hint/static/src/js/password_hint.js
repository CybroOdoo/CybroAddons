/**
 * This module defines a JavaScript file that handles the behavior of the password hint feature on the Odoo login page.
 */
odoo.define('password_hint.login', function (require) {
    'use strict';
     // Import dependencies
    const ajax = require('web.ajax');
    const Dialog = require('web.Dialog');
  /**
     * Handles the behavior of the password hint feature when the "Password Hint" link is clicked.
     */
    $('#Passhint').click(function(){
        var login = $('#login').val();
        if (login){
            ajax.jsonRpc("/website/password/hint", 'call', {
                'params': login
            }).then(function(data){
                if(data){
                    var passwordHint = data;
                    var dialog = new Dialog(null, {
                        title: "Password Hint",
                        size: 'medium',
                        $content: $('<div/>', {
                            html: passwordHint
                        }),
                        buttons: [{
                            text: "Close",
                            close: true
                        }]
                    });
                    dialog.open();
                }
                else {
                    var dialog = new Dialog(null, {
                        title: "Password Hint",
                        size: 'medium',
                        $content: $('<div/>', {
                            html: "No password hint found."
                        }),
                        buttons: [{
                            text: "Close",
                            close: true
                        }]
                    });
                    dialog.open();
                }
            });
        }
    });
});
