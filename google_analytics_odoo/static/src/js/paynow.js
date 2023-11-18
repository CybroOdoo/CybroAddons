/** @odoo-module **/
import core, { _t } from 'web.core';
import checkoutForm from 'payment.checkout_form';
import ajax from 'web.ajax';


checkoutForm.include({
    /**
     * @override _prepareTransactionRouteParams to send events to Analytics
     */
    _prepareTransactionRouteParams: function(code, paymentOptionId, flow) {
        const transactionRouteParams = this._super(...arguments);
        var payment = $('.o_donation_payment_form').length ? {
            ...transactionRouteParams,
            'partner_details': {
                'name': this.$('input[name="name"]').val(),
                'email': this.$('input[name="email"]').val(),
                'country_id': this.$('select[name="country_id"]').val(),
            },
            'donation_comment': this.$('#donation_comment').val(),
            'donation_recipient_email': this.$('input[name="donation_recipient_email"]').val(),
        } : transactionRouteParams;


        ajax.jsonRpc("/get_payment_details", 'call', {'payment':payment}).then(function(data) {
            ajax.jsonRpc("/analytics", 'call', {}).then(function(datas) {
            if (datas.enable_analytics){
                self.measurement_id = datas.measurement_id;
                self.api_secret = datas.api_secret;
                if (self.measurement_id != false && self.api_secret != false) {
                    gtag('get', self.measurement_id, 'client_id', (clientID) => {
                        sendCartEvent(clientID, "Payments", data)
                    });
                }
                //Send the event to Google Analytics when the payments is
                // processed in the website
                function sendCartEvent(clientID, eventName, eventData) {
                    fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                        method: "POST",
                        body: JSON.stringify({
                            client_id: clientID,
                            events: [{
                                name: 'Payments',
                                params: {
                                    "customer": data.partner,
                                    "payment_information": data.payment,
                                    "amount": data.amount
                                }
                            }]
                        })
                    });
                }
                }
            });
        });
        return payment
    },
});
