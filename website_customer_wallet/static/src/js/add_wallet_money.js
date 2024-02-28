/** @odoo-module **/
//Handles the click event on the 'proceed' button to add money to the user's wallet.
var ajax = require('web.ajax');
var rpc = require('web.rpc');
var publicWidget = require('web.public.widget');
var utils = require('web.utils');

publicWidget.registry.WebsiteAddMoney = publicWidget.Widget.extend({
    selector: '#wallet_amount',
    events: {
        'click #proceed': 'WalletAmountProceed',
    },
    WalletAmountProceed: function (ev) {
        var amount = this.$('#wallet_amount').val();
        rpc.query({
            route: "/web/add/money/" + amount,
            params: {
                amount: amount,
            }
        }).then(function (result) {
            window.location.href = '/shop/cart';
            console.log('pppppppp[p[p[p[')
        });
    },
});

var WebsiteAddMoney = new publicWidget.registry.WebsiteAddMoney(this);
WebsiteAddMoney.appendTo($("#wallet_amount"));
return publicWidget.registry.WebsiteAddMoney;
