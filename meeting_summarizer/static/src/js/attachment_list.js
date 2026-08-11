/* @odoo-module */
import { AttachmentList } from "@mail/core/common/attachment_list";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";

patch(AttachmentList.prototype, {
    /**
     * Override: public/guest users (userId === null) cannot download attachments.
     * @param {import("models").Attachment} attachment
     */
    canDownload(attachment) {
        const isPublicUser = user.userId === null;
        if (isPublicUser) {
            return false;
        }
        return super.canDownload(attachment);
    },
});