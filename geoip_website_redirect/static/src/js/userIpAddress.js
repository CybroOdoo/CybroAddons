/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';
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
