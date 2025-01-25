/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { useRef } from "@odoo/owl";
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
        rpc("/shop/attachments" , {
                "attachment_id":attachment_id.id
                 }).then(function (data) {
                        return
        });
        attachment_id.remove();
     },
});
