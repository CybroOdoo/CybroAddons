odoo.define('password_hint.hint', function (require) {
'use strict';
    /* Import dependencies */
    var publicWidget = require('web.public.widget');
    const ajax = require('web.ajax');
    const Dialog = require('web.Dialog');
    /**
     * This widget enhances the behavior of the login form by allowing users to request a password hint
     * based on their entered login value (email). It communicates with the server to retrieve the hint
     * and displays it in a dialog box.
     */
    publicWidget.registry.LoginForm = publicWidget.Widget.extend({
        selector: '.oe_login_form',
        events: {
            'change #login': '_onChangeLogin',
            'click #passwordHint': 'OnClickHint',
        },
        /**
         * Capture login value on change event.
         * @param {Event} ev - The event object representing the change.
         */
        _onChangeLogin: function (ev){
            var loginValue = ''
            this.loginValue = ev.currentTarget.value
        },
        /**
         * Handle the click event on the password hint button.
         * Requests and displays password hint based on login value.
         */
        OnClickHint: function () {
            //Block executes if there is a value in the Email field
            var self = this
            if (this.loginValue) {
                ajax.jsonRpc("/website/password/hint", 'call', {
                    'params': this.loginValue
                }).then(function(data) {
                    if (data) {
                    //If password hint is found returns the password hint.
                        var dialog = new Dialog(null, {
                            title: "Password Hint",
                            size: 'medium',
                            $content: "<div>"+data+"<div>",
                            buttons: [{
                                text: "Close",
                                close: true
                            }]
                        });
                        dialog.open();
                    } else {
                        //Else block to show if the Password Hint is not found for the given Email.
                        var dialog = new Dialog(null, {
                            title: "Password Hint",
                            size: 'medium',
                            $content: "<div>"+'Password Hint not Found'+"<div>",
                            buttons: [{
                                text: "Close",
                                close: true
                            }]
                        });
                        dialog.open();
                    }
                });
            } else {
                //Block executes if there is no value found in Email filed.
                var dialog = new Dialog(null, {
                    title: "Password Hint",
                    size: 'medium',
                    $content: "<div>"+'Please Enter the Email'+"<div>",
                    buttons: [{
                        text: "Close",
                        close: true
                    }]
                });
                dialog.open();
            }
        },
    });
});
