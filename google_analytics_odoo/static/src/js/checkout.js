odoo.define('google_analytics_odoo.checkout', function(require) {
    var publicWidget = require('web.public.widget');
    const ajax = require('web.ajax');

    publicWidget.registry.websiteSaleTracking = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click a[href="/shop/checkout?express=1"]': '_onCheckoutStarts',
        },
        //When an user Checkout the cart then send the event to the Analytics
        _onCheckoutStarts: function(ev) {
            ajax.jsonRpc("/analytics", 'call', {}).then(function(data) {
            if (data.enable_analytics){
                self.measurement_id = data.measurement_id;
                self.api_secret = data.api_secret;
                self.user = data.user
                if (self.measurement_id != false && self.api_secret != false) {
                    gtag('get', self.measurement_id, 'client_id', (clientID) => {
                        sendOfflineEvent(clientID, "Checkout", data)
                    });
                }
                }
            });
            //Send the event to Google Analytics
            function sendOfflineEvent(clientID, eventName, eventData) {
                fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                    method: "POST",
                    body: JSON.stringify({
                        client_id: clientID,
                        events: [{
                            name: 'Cart_checkout',
                            params: {
                                'Checkout': 'checkout started by' + self.user
                            }
                        }]
                    })
                });
            }
        },
        //Override the default _onCheckoutStart function
        _onCheckoutStart: function() {
            this._vpv('/stats/ecom/customer_checkout');
        },
    });
});
