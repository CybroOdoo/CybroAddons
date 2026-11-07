/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },
    /**
     * Handles click on the "Download All Attachments" button.
     */
    async onClickDownloadAttachment(ev) {
        const threadId = this.state.thread?.id || (typeof this.threadId === 'function' ? this.threadId() : this.props?.threadId);
        const threadModel = this.state.thread?.model || (typeof this.threadModel === 'function' ? this.threadModel() : this.props?.threadModel);
        if (!threadId) {
            return;
        }
        // Build the URL with parameters in the query string
        let url = `/chatter/attachments/download/zip?res_id=${threadId}`;
        if (threadModel) {
            url += `&res_model=${encodeURIComponent(threadModel)}`;
        }
        // Send an HTTP GET request to download attachments as a zip file
        fetch(url)
            .then(response => {
                if (response.ok) {
                    return response.blob();
                } else {
                    throw new Error(`Server returned ${response.status} ${response.statusText}`);
                }
            })
            .then(blob => {
                if (blob.size === 0) {
                    this.dialog.add(AlertDialog, {
                        title: _t("Info"),
                        body: _t("There are no attachments to download."),
                    });
                } else {
                    const blobUrl = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = blobUrl;
                    link.download = `attachments_${threadModel || 'chatter'}_${threadId}.zip`;
                    link.click();
                    URL.revokeObjectURL(blobUrl);
                }
            })
            .catch(error => {
                this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("Failed to download attachments. Please check server logs."),
                });
            });
    }
});

