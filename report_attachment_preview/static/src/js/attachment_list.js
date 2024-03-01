/** @odoo-module **/
import { AttachmentList } from "@mail/core/common/attachment_list";
import { patch } from "@web/core/utils/patch";
/**
 This module patches the onClickDownload method of the AttachmentList class
 to open attachments in a new tab when clicked for download.
**/
patch(AttachmentList.prototype, {
    onClickDownload(attachment){
        super.onClickDownload(attachment);
        window.open(attachment.defaultSource);
    }
})