/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.userIpAddress = publicWidget.Widget.extend({
    selector: '.oe_website_login_container',
    events: {
        'click .oe_login_buttons': '_getIpAddress',
    },

    // ✅ Use start() not setup() for legacy widgets
    start: function () {
        this._super.apply(this, arguments);
        return this._getIpAddress();
    },

    _getIpAddress: async function () {
        var self = this;
        await $.getJSON("https://api.ipify.org?format=json", function (data) {
            self.el.querySelector('#user_ip').value = data.ip;
        });
    },
});