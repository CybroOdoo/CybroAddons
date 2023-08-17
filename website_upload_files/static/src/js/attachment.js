odoo.define('website_upload_files.attachment', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    publicWidget.registry.add_attachment = publicWidget.Widget.extend({
        selector: '.div-class-button',
        events: {
            'click #button_add_attachment_payment': 'AttachmentPaymentOnClick',
        },
        /**
        For delete the attachments
        **/
         AttachmentPaymentOnClick: function (ev) {
         var attachment_id = ev.target.closest('div')
            ajax.jsonRpc("/shop/attachments", 'call', {
                    "attachment_id":attachment_id.id
                     })
            .then(function (data) {
                return
            });
            attachment_id.remove();
         },
    });
    return publicWidget.registry.add_attachment
});
