/** @odoo-module **/
// Handles the click event on the 'change_button' to change the user's PIN.
var rpc = require('web.rpc');
import { qweb, _t } from 'web.core';
var publicWidget = require('web.public.widget');
var session = require('web.session');

publicWidget.registry.WebsiteChangePin = publicWidget.Widget.extend({
    selector: '#re_login_data',
    events: {
        'click #change_button': 'ChangePin',
    },
    ChangePin: function (ev) {
        ev.preventDefault();
        var current_pswd = this.$("#current_pswd").val();
        var new_pswd = this.$("#new_confirm_pswd").val();
        rpc.query({
            model: "res.users",
            method: "change_pin",
            args: [[], { 'current_pswd': current_pswd, 'new_pswd': new_pswd }],
        }).then(function (result) {
            if (result == false) {
                $('.change_pin').removeClass('d-none');
                $('.forgot_pin').addClass('d-none');
            } else {
                $('.wrong_change_pin').removeClass('d-none');
                $('.wrong_loginn').addClass('d-none');
            }
        });
    },
});

var WebsiteChangePin = new publicWidget.registry.WebsiteChangePin(this);
WebsiteChangePin.appendTo($("#re_login_data"));
return publicWidget.registry.WebsiteChangePin;
