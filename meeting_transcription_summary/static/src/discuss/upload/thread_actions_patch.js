/** @odoo-module **/

import { registerThreadAction } from "@mail/core/common/thread_actions";
import { UploadRecordingDialog } from "./upload_recording_dialog";
import { _t } from "@web/core/l10n/translation";

registerThreadAction("upload-meeting-recording", {
    // internal users only, like the upload route and the summary's access rights
    condition: ({ store, thread }) =>
        thread?.model === "discuss.channel" && store?.self_partner?.main_user_id?.share === false,
    icon: "fa fa-fw fa-file-video-o",
    name: _t("Upload Meeting Recording"),
    open({ store, thread }) {
        store.env.services.dialog.add(UploadRecordingDialog, {
            thread,
            close: () => {},
        });
    },
    sequence: 35,
});
