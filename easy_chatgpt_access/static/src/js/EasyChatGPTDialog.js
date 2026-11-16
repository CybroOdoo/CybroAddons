/** @odoo-module */
import { Component, proxy, signal, onPatched, markup, useProps, t } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

export class EasyChatGPTDialog extends Component {
    static components = { Dialog };
    static template = "easy_chatgpt_access.EasyChatGPTDialog";

    props = useProps({
        close: t.function().optional(),
        systray: t.object().optional({ insert: false }),
        insert: t.function().optional(),
        sanitize: t.function().optional(),
    });

    messagesContainerRef = signal.ref();

    setup() {
        this.notificationService = useService("notification");
        this.state = proxy({
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

        // Auto-scroll to bottom whenever the component re-renders
        onPatched(() => {
            this._scrollToBottom();
        });
    }

    _cancel() {
        this.props.close();
    }

    _confirm() {
        if (this.props.systray?.insert && this.props.insert) {
            const lastMessage = this.state.messages[this.state.messages.length - 1];
            if (lastMessage && !lastMessage.isError) {
                this.props.insert(lastMessage.text);
            }
        }
        this.props.close();
    }

    formatContent(content) {
        if (!content) {
            return "";
        }
        const escaped = content
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        return markup(escaped.replace(/\n/g, "<br/>"));
    }

    async generate(prompt, callback) {
        try {
            const content = await rpc("/html_editor/generate_text", {
                prompt,
                conversation_history: this.state.conversationHistory,
            }, { silent: true });
            callback(content, false);
        } catch (error) {
            callback(error.data?.message || error.message || "Failed to generate text", true);
        }
    }

    /**
     * URL for the current user's profile photo.
     * Uses user.userId from @web/core/user.
     */
    get userAvatarUrl() {
        return `/web/image/res.users/${user.userId}/image_128`;
    }

    /**
     * URL for the bot avatar – uses the dedicated ChatGPT SVG avatar.
     */
    get botAvatarUrl() {
        return "/easy_chatgpt_access/static/src/img/img.png";
    }

    _scrollToBottom() {
        const el = this.messagesContainerRef();
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
            } catch (_err) {
                this.notificationService.add("Failed to copy text", {
                    type: 'danger',
                    title: 'Copy Failed',
                    sticky: false,
                });
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
