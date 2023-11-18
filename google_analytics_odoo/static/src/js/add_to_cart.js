/** @odoo-module **/
import { WebsiteSale } from 'website_sale.website_sale';
import ajax from 'web.ajax';

WebsiteSale.include({
    /**
     * @Super the _onClickAdd function to send the event to the Analytics
     */
    _onClickAdd: function(ev) {
        this._super(...arguments);
        var self = this;
        if (ev.currentTarget.previousElementSibling) {
            this.product_id = ev.currentTarget.previousElementSibling.value
        } else {
            this.product_id = this.last_product_id
        }
        ajax.jsonRpc("/product_analytics", 'call', {'product_id':this.product_id}).then(function(data) {
            ajax.jsonRpc("/analytics", 'call', {}).then(function(datas) {
                if (datas.enable_analytics)
                {
                self.measurement_id = datas.measurement_id;
                self.api_secret = datas.api_secret;
                if (self.measurement_id != false && self.api_secret != false) {
                    gtag('get', self.measurement_id, 'client_id', (clientID) => {
                        sendCartEvent(clientID, "AddToCart", data[0])
                    });
                }
                }
            });
            // Sending the event to Google Analytics when the user adds a new
            // product to the shopping cart.
            function sendCartEvent(clientID, eventName, eventData) {
                fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                    method: "POST",
                    body: JSON.stringify({
                        client_id: clientID,
                        events: [{
                            name: 'Add_to_cart',
                            params: {
                                "currency": eventData['currency_id'][1],
                                "value": eventData['lst_price'],
                                "item_id": eventData['id'],
                                "item_name": eventData['display_name'],
                                "price": eventData['lst_price'],
                            }
                        }]
                    })
                });
            }
        });
    }
});
