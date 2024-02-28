/** @odoo-module **/
var rpc = require('web.rpc');
var publicWidget = require('web.public.widget');
const { Component } = owl;

publicWidget.registry.WebsiteForgotPin = publicWidget.Widget.extend({
    selector: '.change_pin_form',
    events: {
        'submit': 'Validation',
        'click #go_back_submit': 'GoBack'
    },
    // Handles the form submission event for PIN validation and communication with the server.
    Validation: function (ev) {
        ev.preventDefault();
        var current_pswd = this.$("#new_pswd").val();
        var new_pswd = this.$("#new_confirm_pswd").val();
        if (current_pswd !== new_pswd) {
            $('.wrong_forgot_pin').removeClass('d-none');
        }
        rpc.query({
            route: "/web/re_check/pin/",
            params: {
                new_pswd: new_pswd
            }
        }).then(function (result) {
            $('.login_none').removeClass('d-none');
            $('.forgot_pin_number').addClass('d-none');
        });
    },
    // Handles the 'Go Back' click event, allowing users to return to the login screen.
    GoBack: function (ev) {
        $('.login_none').removeClass('d-none');
        $('.forgot_pin_number').addClass('d-none');
    }
});

var WebsiteForgotPin = new publicWidget.registry.WebsiteForgotPin(this);
WebsiteForgotPin.appendTo($("#re_login_data"));
return publicWidget.registry.WebsiteForgotPin;
