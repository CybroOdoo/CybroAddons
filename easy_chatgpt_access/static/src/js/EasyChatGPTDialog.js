/** @odoo-module */
import { ChatGPTDialog } from "@html_editor/main/chatgpt/chatgpt_dialog";
import { useState, useRef, onPatched } from "@odoo/owl";
import { user } from "@web/core/user";

export class EasyChatGPTDialog extends ChatGPTDialog {
    static template = "easy_chatgpt_access.EasyChatGPTDialog";
    static props = {
        ...super.props,
        systray: { type: Object, optional: true },
    };
    static defaultProps = {
        ...super.defaultProps,
        systray: {
            insert: false,
        },
    };

    setup() {
        super.setup();
        this.state = useState({
            ...this.state,
            prompt: "",
            messages: [],
            conversationHistory: [
                {
                    role: "system",
                    content: "You are a helpful assistant.",
                },
            ],
            isGenerating: false,
        });

        // Ref for auto-scrolling the messages container
        this.messagesContainer = useRef("messagesContainer");

        // Auto-scroll to bottom whenever the component re-renders
        onPatched(() => {
            this._scrollToBottom();
        });
    }

    /**
     * URL for the current user's profile photo.
     * Uses user.userId from @web/core/user (session.uid is deleted in Odoo 19).
     */
    get userAvatarUrl() {
        return `/web/image/res.users/${user.userId}/image_128`;
    }

    /**
     * URL for the bot avatar – uses the Odoo superuser (uid=1) profile photo.
     */
    get botAvatarUrl() {
        return `/web/image/res.users/1/image_128`;
    }

    _scrollToBottom() {
        const el = this.messagesContainer.el;
        if (el) {
            el.scrollTop = el.scrollHeight;
        }
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.onGenerate();
        }
    }

    async onGenerate() {
        if (!this.state.prompt.trim()) {
            return;
        }
        const prompt = this.state.prompt;
        this.state.prompt = "";
        this.state.isGenerating = true;

        const messageId = new Date().getTime();
        this.state.messages.push({
            author: "user",
            text: prompt,
            id: messageId - 1,
        });

        await this.generate(prompt, (content, isError) => {
            this.state.isGenerating = false;
            if (!isError) {
                this.state.conversationHistory.push(
                    { role: "user", content: prompt },
                    { role: "assistant", content }
                );
            }
            this.state.messages.push({
                author: "assistant",
                text: content,
                id: messageId,
                isError,
            });
            this.state.selectedMessageId = messageId;
        });
    }

    async copyMessage(ev) {
        const messageId = ev.currentTarget.getAttribute("data-message-id");
        const message = this.state.messages.find(m => m.id == messageId);
        if (message && message.text) {
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(message.text);
                } else {
                    const fallbackTextArea = document.createElement("textarea");
                    fallbackTextArea.value = message.text;
                    fallbackTextArea.style.position = "fixed"; // prevent scroll
                    fallbackTextArea.style.opacity = "0";
                    document.body.appendChild(fallbackTextArea);
                    fallbackTextArea.select();
                    document.execCommand("copy");
                    document.body.removeChild(fallbackTextArea);
                }
                this.notificationService.add("Text copied to Clipboard", {
                    type: 'success',
                    title: 'Text copied',
                    sticky: false,
                });
            } catch (err) {
                this.notificationService.add("Failed to copy text", {
                    type: 'danger',
                    title: 'Copy Failed',
                    sticky: false,
                });
                console.error("Clipboard copy failed", err);
            }
        }
    }

    onAvatarError(ev) {
        // When the profile photo is missing, replace the broken img with a
        // Font Awesome icon inside a styled circle so the layout stays intact.
        const img = ev.currentTarget;
        const iconClass = img.getAttribute("data-fallback") || "fa-user";
        const isUser = img.classList.contains("user-avatar");
        const wrapper = img.parentElement;
        if (wrapper) {
            wrapper.innerHTML = `<span class="o-chatgpt-avatar-fallback ${isUser ? 'user-avatar' : 'bot-avatar'}"><i class="fa ${iconClass}"></i></span>`;
        }
    }
}
