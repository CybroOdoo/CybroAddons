/** @odoo-module **/

import { AttachmentUploadService } from "@mail/core/common/attachment_upload_service";
import { patch } from "@web/core/utils/patch";

patch(AttachmentUploadService.prototype, {
    _processLoaded(thread, composer, response, tmpId, resolveUpload) {
        if (response.size_error) {
            this.notificationService.add(response.size_error, {
                type: "danger",
                sticky: false,
            });
            resolveUpload();
            this._cleanupUploading(tmpId);
            return;
        }
        super._processLoaded(thread, composer, response, tmpId, resolveUpload);
    }
});
