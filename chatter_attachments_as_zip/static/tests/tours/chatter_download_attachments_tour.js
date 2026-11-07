/** @odoo-module **/
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("chatter_download_attachments_tour", {
    steps: () => [
        {
            content: "Check that attachment box is present in chatter",
            trigger: ".o-mail-AttachmentBox",
        },
        {
            content: "Check that download all attachments button is visible",
            trigger: ".o-mail-AttachmentBox button:contains('Download All Attachments')",
            run: "click",
        },
    ],
});

