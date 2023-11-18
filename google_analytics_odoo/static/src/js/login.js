/** @odoo-module **/
import publicWidget from 'web.public.widget';
import ajax from 'web.ajax';

publicWidget.registry.login = publicWidget.Widget.extend({
    selector: '.oe_login_form',
    events: {
        'click button[type="submit"]': '_onLogIn',
    },
    /**
     * @override the _onLogIn function to override the default workflow of login
     */
    _onLogIn: async function(ev) {
        var self = this;
        await ajax.jsonRpc('/analytics', 'call', {}).then((result) => {
            self.measurement_id = result.measurement_id
            self.api_secret = result.api_secret
            self.enable_analytics = result.enable_analytics
        });
        if (self.enable_analytics){
        if (self.measurement_id != false && self.api_secret != false) {
            gtag('get', self.measurement_id, 'client_id', (clientID) => {
                sendLoginEvent(clientID, "LOGIN")
            });
            var user = this.$("#login").val()
            // Send the events to Analytics When a user is logged in
            function sendLoginEvent(clientID, eventName) {
                fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                    method: "POST",
                    body: JSON.stringify({
                        client_id: clientID,
                        events: [{
                            name: 'User_login',
                            params: {
                                "User": user
                            }
                        }]
                    })
                });
            }
        }
        }
    }
});
