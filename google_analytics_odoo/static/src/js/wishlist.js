    /** @odoo-module **/
import publicWidget from 'web.public.widget';
import 'website_sale_wishlist.wishlist';
import ajax from 'web.ajax';

publicWidget.registry.ProductWishlist.include({
    /**
     * Removes wishlist indication when adding a product to the wishlist.
     *
     * @override function to send the event to the Analytics
     */
    _onClickAddWish: function(ev) {
        this._super.apply(this, arguments);
        if (ev.currentTarget.attributes[10]){
        var product_id = ev.currentTarget.attributes[10].value
        ajax.jsonRpc("/product_analytics", 'call', {'product_id':this.product_id}).then(function(data) {
            ajax.jsonRpc("/analytics", 'call', {}).then(function(datas) {
            if (datas.enable_analytics){
                self.measurement_id = datas.measurement_id;
                self.api_secret = datas.api_secret;
                gtag('get', self.measurement_id, 'client_id', (clientID) => {
                    sendOfflineEvent(clientID, "AddToWishlist", data[0])
                });
                }
            });
            // Sending the event to Google Analytics when the user adds a new
            // product to the shopping cart.
            function sendOfflineEvent(clientID, eventName, eventData) {
                var send_data = fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                    method: "POST",
                    body: JSON.stringify({
                        client_id: clientID,
                        events: [{
                            name: 'Add_to_wishlist',
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
    },
});
