/** @odoo-module **/
import { ChatGPTDialog } from '@web_editor/js/wysiwyg/widgets/chatgpt_dialog';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
/**
 * Patch ChatGPTDialog for modifying the setup and adding copyMessage function.
 * Modifies the setup function to include initialization of the 'action' service.
 * Adds the copyMessage function to copy generated AI text into the clipboard and display a notification.
 */
patch(ChatGPTDialog.prototype, {
    setup() {
        super.setup(...arguments);
        this.action = useService('action');
        this.notification = useService("notification");
    },
    // Copy the generated AI text into clipboard when hitting the Copy button
    copyMessage(ev) {
        var content = ev.target.parentElement.children[1].innerText
        const message = "Copied to Clipboard!"
        var textArea = document.createElement("textarea");
        textArea.value = content;
        document.body.appendChild(textArea);
        textArea.select();
        var successful = document.execCommand('copy');
        document.body.removeChild(textArea)
        this.displayNotification(
           ("Text copied to Clipboard")
        );
        return successful;
    },
    displayNotification(text) {
        this.notification.add(text, {
           type: 'success',
           title: 'Text copied',
           sticky: false,
        });
    }
})
