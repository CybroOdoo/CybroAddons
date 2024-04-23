/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },
    /**
     * Handles click on the "add attachment" button.
     */
    async onClickDownloadAttachment(ev) {
        // Build the URL with parameters in the query string
        const url = `/chatter/attachments/download/zip?res_id=${this.props.threadId}`;
        // Send an HTTP GET request to download attachments as a zip file
        fetch(url)
            .then(response => {
                if (response.ok) {

                    // Create a Blob from the response data
                    return response.blob();
                } else {
                    throw new Error('Failed to fetch');
                }
            })
            .then(blob => {
                if (blob.size == 0) {
                    this.dialog.add(AlertDialog, {
                        title: _t("Info"),
                        body: _t("There are no attachments to download."),
                    });
                } else {
                    // Create a URL for the Blob
                    const blobUrl = URL.createObjectURL(blob);
                    // Create an anchor element for downloading
                    const link = document.createElement('a');
                    link.href = blobUrl;
                    link.download = `attachments${this.props.threadId}.zip`;
                    // Trigger a click event to start the download
                    link.click();
                    // Clean up by revoking the Blob URL
                    URL.revokeObjectURL(blobUrl);
                }
            })
    }
})
