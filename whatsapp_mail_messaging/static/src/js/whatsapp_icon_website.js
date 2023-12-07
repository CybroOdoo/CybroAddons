odoo.define('whatsapp_mail_messaging.whatsapp_icon_website.js', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');


    publicWidget.registry.WhatsappIcon = publicWidget.Widget.extend({
        selector: '.cy_whatsapp_web',
        events: {
                'click': '_onClickWhatsappIcon',
        },
        start: function() {
            this._super.apply(this, arguments);
        },
        _onClickWhatsappIcon: function (ev) {
                $('#ModalWhatsapp').css('display', 'block');
        },
    });
});