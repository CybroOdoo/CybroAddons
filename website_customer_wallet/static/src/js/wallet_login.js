/** @odoo-module **/
// When the form is submitted, it checks the entered PIN with the server and redirects to the wallet info page if the PIN is correct.
var rpc = require('web.rpc');
import { qweb, _t } from 'web.core';
var publicWidget = require('web.public.widget');

publicWidget.registry.WebsiteCustomerWallet = publicWidget.Widget.extend({
selector: '.login_form',
 events: {
        'submit': '_onSubmit',
        'click #forgot_login_pin': 'ReLogin'
    },
    //Handles the form submission event for PIN validation and redirection to the wallet info page.
    _onSubmit: function (ev) {
    ev.preventDefault();
    var data=this.$("#user_id").val();
    var data_name=this.$('#user_name').val();
    var pin=this.$('#login_value').val();
    console.log(data,'ererrerrtryygy')
    console.log(data_name,'ererrerrtryygy')
    console.log(pin,'ererrerrtryygy')
    rpc.query({
                route: "/web/check/pin/"+pin,
                params: {
                    pin:pin
                }
                })
                .then(function (result) {
                if(result==true){
                  console.log(result,'000-ew0-e9e8e')
                  window.location.href = '/my/wallet/info';
                  }
                  else{
                        $('.wrong_loginn').removeClass('d-none');
                       }
                         })
       },
       //Handles the 'Forgot Login PIN' click event, initiating the process of recovering or changing the PIN.
    ReLogin: function (ev) {
            ev.preventDefault();
            $('.login_none').addClass('d-none');
            $('.forgot_pin_number').removeClass('d-none')
            },
});

    var WebsiteCustomerWallet = new publicWidget.registry.WebsiteCustomerWallet(this);
    WebsiteCustomerWallet.appendTo($(".login_form"));
    return publicWidget.registry.WebsiteCustomerWallet;
