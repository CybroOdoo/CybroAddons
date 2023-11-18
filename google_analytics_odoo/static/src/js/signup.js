odoo.define('google_analytics_odoo.signup', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    const ajax = require('web.ajax');

    publicWidget.registry.SignUpForm = publicWidget.Widget.extend({
        selector: '.oe_signup_form',
        events: {
            'submit': '_onSubmit',
        },
         /**
         * @override the _onSubmit function to override the default workflow of sign up
         */
        _onSubmit: async function(ev) {
            var self = this;
            await ajax.jsonRpc('/analytics', 'call', {}).then((result) => {
                self.measurement_id = result.measurement_id
                self.api_secret = result.api_secret
                self.enable_analytics = result.enable_analytics
            });
            if (self.enable_analytics){
            if (self.measurement_id != false && self.api_secret != false) {
                var user_name = this.$("#name").val()
                var mail = this.$("#login").val()
                gtag('get', self.measurement_id, 'client_id', (clientID) => {
                    sendSignupEvent(clientID, "SIGNUP")
                });
            // Send the events to Analytics When a user is signed up
                function sendSignupEvent(clientID, eventName) {
                    fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${self.measurement_id}&api_secret=${self.api_secret}`, {
                        method: "POST",
                        body: JSON.stringify({
                            client_id: clientID,
                            events: [{
                                name: 'Signup_user',
                                params: {
                                    "Name": user_name,
                                    "Mail": mail,
                                }
                            }]
                        })
                    });
                }
            }
            }
        },
    });
});
