    /** @odoo-module **/
    //It provides a widget that listens for click events on various buttons and displays different templates
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var publicWidget = require('web.public.widget');
    var utils = require('web.utils');

    publicWidget.registry.WebsiteWalletInfo = publicWidget.Widget.extend({
     selector: '.buttons',
       events: {
           'click #add_money': 'AddMoneyTemplate',
           'click #passbook': 'PassBookTemplate',
           'click #change_pin_button': 'ChangePinTemplate',
       },
       //Displays the wallet money template when the 'Add Money' button is clicked.
     AddMoneyTemplate:function(ev) {
             $('.wallet_money').removeClass('d-none');
             $('.forgot_pin').addClass('d-none');
             $('.wallet_history').addClass('d-none');
             $('#success_info').addClass('d-none')
             $('.change_pin').addClass('d-none');
        },
        //Displays the wallet history template when the 'Passbook' button is clicked.
     PassBookTemplate:function(ev) {
            $('.wallet_history').removeClass('d-none');
            $('.forgot_pin').addClass('d-none');
            $('.wallet_money').addClass('d-none');
            $('#success_info').addClass('d-none');
            $('.change_pin').addClass('d-none');
            rpc.query({
              'route':'/web/wallet/transactions/',
              'params':{}
            }).then(function(data) {
                    $('.wallet_history').empty().append(data);
                });
        },
        //Displays the forgot PIN template when the 'Change PIN' button is clicked.
    ChangePinTemplate:function(ev) {
            $('.wallet_money').addClass('d-none');
            $('.wallet_history').addClass('d-none');
            $('.forgot_pin').removeClass('d-none');
            $('#success_info').addClass('d-none');
            $('.change_pin').addClass('d-none');
            $('.wrong_login').addClass('d-none');
        },
    });

    var WebsiteWalletInfo = new publicWidget.registry.WebsiteWalletInfo(this);
        WebsiteWalletInfo.appendTo($(".buttons"));
        return publicWidget.registry.WebsiteWalletInfo;
