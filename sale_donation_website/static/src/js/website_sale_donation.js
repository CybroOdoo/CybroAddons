//To pass selected donations in to the sale order
odoo.define('sale_donation_website.donation', function(require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    publicWidget.registry.donation = publicWidget.Widget.extend({
    selector: '.donation',
    events: {
        'change .form-check-input': '_onCheckDonation',
    },
    _onCheckDonation: function (ev) {
        var donation = $(ev.currentTarget);
        var isChecked = donation.is(':checked');
        this._rpc({
            route: '/shop/update_donation',
            params: {
                donation_id: donation.val(),
                checked: isChecked,
            },
        });
    },
    });
     var donationButton = $('button[name="donation_submit_button"]');
     donationButton.click(function() { window.location.reload(); });
});
