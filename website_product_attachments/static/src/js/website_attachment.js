/* @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
publicWidget.registry.AttachmentTab = publicWidget.Widget.extend({
//    Extend public widget to add the attachment in the product.
    selector: ".js_attachment_container",
    events: {
        'click .js_on_click_show_attachment': 'onClickAttachment',
    },
    onClickAttachment: function(ev) {
    //Function for attachment opening.
        const attachmentId = ev.currentTarget.getAttribute('data-value')
        const url = `/attachment/download?attachment_id=${attachmentId}`
        window.open(url, '_blank');
    }
})
