import { AttachmentList } from "@mail/core/common/attachment_list";
import { patch } from "@web/core/utils/patch";

/**
 * Also open chatter attachments in a new browser tab when they are
 * downloaded. Files a browser cannot show are only downloaded, as a new tab
 * would stay blank and download them a second time.
 */
patch(AttachmentList.prototype, {
    onClickDownload(attachment) {
        super.onClickDownload(attachment);
        if (attachment.isViewable) {
            window.open(attachment.defaultSource);
        }
    },
});
