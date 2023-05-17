odoo.define('geoip_website_redirect.get_ip', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
//public widget for getting the IP address of the user
    publicWidget.registry.userIpAddress = publicWidget.Widget.extend({
         selector: '.oe_website_login_container',
         events: {
             'click .oe_login_buttons': '_getIpAddress',
        },
        setup(){
            super.setup();
            this._getIpAddress()
        },
//function which give ip address of user
        _getIpAddress: async function(events){
             var self = this;
             await $.getJSON("https://api.ipify.org?format=json", function(data) {
                self.el.querySelector('#user_ip').value = data.ip;
            });
        },
    });

    return publicWidget.registry.userIpAddress;
    });
