/** @odoo-module */

import { useRef } from "@odoo/owl";
import { MessagingMenu } from "@mail/core/web/messaging_menu";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { Picker, usePicker } from "@mail/core/common/picker";
import { useEmojiPicker } from "@web/core/emoji_picker/emoji_picker";


patch(MessagingMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.textareaRefs = [];
        var reply_button = document.getElementById("reply_button");
        var reply_msg = document.getElementById("reply_message");
        var send_reply = document.getElementById("send_reply");
        var emoji_reply = document.getElementById("emoji_reply");
        console.log(emoji_reply, 'emoji_reply.emoji_reply')
        this.emojiRef = useRef('emoji-button')
        this.inputRef = useRef('textarea')
        this.textareaRefs = this.messages
        this.emojiPicker = useEmojiPicker(this.emojiRef, {onSelect : this.emojiSelect.bind(this)})
    },
     emojiSelect(ev){
        var inputText = this.inputRef.el.value
        var cursorPosition = this.inputRef.el.selectionStart;
        var updatedText = inputText.substring(0, cursorPosition) +
            ev + inputText.substring(cursorPosition);
        this.inputRef.el.value = updatedText
    },

    async composeMessage(ev, thread){
    if (ev.key === "Enter") {
            this.thread = thread
            await this.threadService.post(this.thread, this.inputRef.el.value);
        }
    },
    onClickReply(message, thread) {
        const inputString = message.body;
        this.message = message;
        this.clickedAuthor = message.author;
        const match = inputString.match(/<p>(.*?)<\/p>/);
        const result = match ? match[1] : null;
        this.message = result
        this.clickedAuthor = this.message.author;
        this.reply_button = document.getElementById("reply_button");
        this.reply_msg = document.getElementById("reply_message");
        this.send_reply = document.getElementById("send_reply");
        this.emoji_reply = document.getElementById("emoji_reply");
        this.reply_button.style.display = "none";
        this.reply_msg.style.display = "block";
        this.send_reply.style.display = "block";
        this.emoji_reply.style.display = "block";
    },
    async onClickSendReply(ev) {
        this.thread = ev
        const value = this.reply_msg.value
        await this.threadService.post(this.thread, value);
        this.reply_msg.style.display = "none";
        this.send_reply.style.display = "none";
    },
});
