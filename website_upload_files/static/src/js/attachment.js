import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class AttachmentDelete extends Interaction {
    static selector = ".div-class-button";
    dynamicContent = {
        ".js_delete_attachment": {
            "t-on-click.prevent.stop": this.onDeleteAttachment,
        },
    };

    /**
     * Handles attachment deletion
     * @param {MouseEvent} ev
     */
    async onDeleteAttachment(ev) {
        const button = ev.currentTarget;
        if (!button) {
            return;
        }
        const itemContainer = button.closest(".js_attachment_item");
        if (!itemContainer) {
            return;
        }

        const attachmentId = itemContainer.dataset.id;
        if (!attachmentId) {
            return;
        }

        // Remove item from DOM immediately for instant UI feedback
        itemContainer.remove();

        try {
            await this.waitFor(rpc("/shop/attachments", {
                attachment_id: parseInt(attachmentId, 10),
            }));
        } catch (error) {
            console.error("Failed to delete attachment:", error);
        }
    }
}

registry
    .category("public.interactions")
    .add("website_upload_files.attachment_delete", AttachmentDelete);


