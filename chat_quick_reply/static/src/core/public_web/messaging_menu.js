/** @odoo-module */
import { useRef, toRaw } from "@odoo/owl";
import { MessagingMenu } from "@mail/core/public_web/messaging_menu";
import { patch } from "@web/core/utils/patch";
import { useEmojiPicker } from "@web/core/emoji_picker/emoji_picker";
import { isEventHandled, markEventHandled } from "@web/core/utils/misc";
import { useSelection } from "@mail/utils/common/hooks";


patch(MessagingMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.textareaRefs = [];
        this.emojiRef = useRef('emoji-button')
        this.emojiChannelRef = useRef('emoji-channel-button')
        this.inputRef = useRef('input_reply')
        this.inputRefChannel = useRef('input_reply_channel')
        this.textareaRefs = this.messages
        this.selection = useSelection({
            refName: "textarea",
            model: this.store.Composer.selection,
            preserveOnClickAwayPredicate: async (ev) => {
                // Let event be handled by bubbling handlers first.
                await new Promise(setTimeout);
                return (
                    !this.isEventTrusted(ev) ||
                    isEventHandled(ev, "sidebar.openThread") ||
                    isEventHandled(ev, "emoji.selectEmoji") ||
                    isEventHandled(ev, "Composer.onClickAddEmoji") ||
                    isEventHandled(ev, "Composer.onClickAddEmojiChannel") ||
                    isEventHandled(ev, "composer.clickOnAddAttachment") ||
                    isEventHandled(ev, "composer.selectSuggestion")
                );
            },
        });
        this.emojiPicker = useEmojiPicker(this.emojiRef, {
            onSelect: this.emojiSelect.bind(this)
        })
        this.emojiPickerChannel = useEmojiPicker(this.emojiChannelRef, {
            onSelect: this.emojiSelectChannel.bind(this)
        })
    },
    // Function to select the chats and add emojis
    emojiSelect(ev){
        var inputText = this.inputRef.el.value
        var cursorPosition = this.inputRef.el.selectionStart;
        var updatedText = inputText.substring(0, cursorPosition) +
            ev + inputText.substring(cursorPosition);
        this.inputRef.el.value = updatedText
    },
    // Function to select the channel messages and add emojis
    emojiSelectChannel(ev){
        var inputText = this.inputRefChannel.el.value
        var cursorPosition = this.inputRefChannel.el.selectionStart;
        var updatedText = inputText.substring(0, cursorPosition) +
            ev + inputText.substring(cursorPosition);
        this.inputRefChannel.el.value = updatedText
    },
    // Function to work on clicking the emoji popup for chats
    onClickAddEmoji(ev) {
        if (!this.emojiPicker) {
            this.emojiPicker = useEmojiPicker(this.emojiRef, {
                onSelect: this.emojiSelect.bind(this)
            });
        }
        this.emojiPicker.toggle?.();
        markEventHandled(ev, "Composer.onClickAddEmoji");
    },
    // Function to work on clicking the emoji popup for channel messages
    onClickAddEmojiChannel(ev) {
        if (!this.emojiPickerChannel) {
            this.emojiPickerChannel = useEmojiPicker(this.emojiChannelRef, {
                onSelect: this.emojiSelectChannel.bind(this)
            });
        }
        if (this.emojiPickerChannel) {
            this.emojiPickerChannel.toggle?.();
        } else {
            console.error("emojiPickerChannel not initialized");
        }
        markEventHandled(ev, "Composer.onClickAddEmojiChannel");
    },
    // Function to compose the message while clicking the enter button
    async composeMessage(ev, thread){
    if (ev.key === "Enter") {
        const postThread = toRaw(thread);
        const post = postThread.post.bind(postThread, this.replay_section.querySelector('.input_message').value);
            if (postThread.model === "discuss.channel") {
                post();
            } else {
                await post();
            }
        }
    },
    // Function to toggle the visibility of the reply buttons
    onClickReply(message) {
        this.replay_section = event.target.parentNode.querySelector('.replay_section')
        event.target.style.display = "none";
        this.replay_section.style.display = "block";
        const inputString = message.body;
        this.message = message;
        this.clickedAuthor = message.author;
        const match = inputString.match(/<p>(.*?)<\/p>/);
        const result = match ? match[1] : null;
        this.message = result
        this.clickedAuthor = this.message.author;
    },
    // Actual  compose of  the message
    async onClickSendReply(ev) {
        this.thread = ev
        const postThread = toRaw(this.thread);
        const post = postThread.post.bind(postThread, this.replay_section.querySelector('.input_message').value);
        if (postThread.model === "discuss.channel") {
            this.replay_section.style = "none"
            post();
        } else {
            await post();
        }
    },
});
