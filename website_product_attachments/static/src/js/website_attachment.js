/* @odoo-module */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class AttachmentTab extends Interaction {
    static selector = ".js_attachment_container";
    dynamicContent = {
        ".js_on_click_show_attachment": {
            "t-on-click": this.onClickAttachment,
        },
    };

    onClickAttachment(ev) {
        ev.preventDefault();
        const attachmentId = ev.currentTarget.dataset.value;
        const url = `/attachment/download?attachment_id=${attachmentId}`;
        window.open(url, "_blank");
    }
}

registry
    .category("public.interactions")
    .add("website_product_attachments.AttachmentTab", AttachmentTab);
