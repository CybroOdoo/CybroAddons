/** @odoo-module **/
var rpc = require('web.rpc');
var publicWidget = require('web.public.widget');

publicWidget.registry.WebsiteTransfer = publicWidget.Widget.extend({
    selector: '#AmountTransferForm',
    events: {
        'submit': '_onSubmit',
    },
    _onSubmit: function (e) {
        e.preventDefault();
        var number = $("#number").val();
        var amount = $('#amount').val();
        rpc.query({
            model: 'loyalty.card',
            method: 'wallet_amount',
            args: [[], { 'number': number, 'amount': amount }],
        }).then(function (ev) {
            if (ev == false) {
                alert("Please specify the right number or correct amount.");
            } else {
                $('#wrong_login').removeClass('d-none');
                $('#success_info').removeClass('d-none');
                location.reload();
            }
        });
    }
});

var WebsiteTransfer = new publicWidget.registry.WebsiteTransfer(this);
WebsiteTransfer.appendTo($("#AmountTransferForm"));
return publicWidget.registry.WebsiteTransfer;
