/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Composer } from "@mail/core/common/composer";
import { CameraDialog } from "./camera_dialog";
import { useService } from "@web/core/utils/hooks";

patch(Composer.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },

    onClickCamera() {
        this.dialog.add(CameraDialog, {
            onCapture: this.onCapture.bind(this),
        });
    },

    async onCapture(file) {
        if (this.attachmentUploader) {
            await this.attachmentUploader.uploadFile(file);
        } else {
            console.error("Attachment uploader not found on Composer.");
        }
    }
});
