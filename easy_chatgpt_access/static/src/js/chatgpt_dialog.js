/** @odoo-module */
import { ChatGPTTranslateDialog } from "@html_editor/main/chatgpt/chatgpt_translate_dialog";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ChatGPTTranslateDialog.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
    },

    async copyMessage(ev) {
        const messageId = ev.currentTarget.getAttribute("data-message-id");
        const message = this.state.messages.find(m => m.id == messageId);
        if (message && message.text) {
            await navigator.clipboard.writeText(message.text);
            this.displayNotification("Text copied to Clipboard");
        }
    },

    displayNotification(text) {
        this.notification.add(text, {
            type: 'success',
            title: 'Text copied',
            sticky: false,
        });
    }
});
