/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillStart, markup } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AiChatWindow extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.rpc = useService("rpc");
        this.messageInputRef = useRef("messageInput");
        this.messagesContainerRef = useRef("messagesContainer");
        this.fileInputRef = useRef("fileInput");


        this.state = useState({
            messages: [],
            isTyping: false,
            pinned: true,
            sessionId: null,
            showModelSwitcher: false,
            selectedSwitcherProviderId: null,
            providers: [],
            attachments: [],
        });


        onWillStart(async () => {
            if (!this.props.agentId) {
                // Fetch default/active agent if not provided
                const providerInfo = await this.rpc("/ai_chat/get_active_provider");
                if (providerInfo.success) {
                    this.state.activeAgentId = providerInfo.agent_id;
                    this.state.activeModelId = providerInfo.model_id;
                    this.state.activeAgentName = providerInfo.agent_name;
                }
            } else {
                this.state.activeAgentId = this.props.agentId;
                this.state.activeModelId = this.props.modelId;
                this.state.activeAgentName = this.props.agentName;
            }
            await this.loadMessages();
            await this.loadProviders();
        });

        onMounted(() => {
            this.autoResizeTextarea();
            this.scrollToBottom();
            
            // Explicitly focus the input when mounted
            const messageInput = this.messageInputRef.el;
            if (messageInput) {
                setTimeout(() => {
                    messageInput.focus();
                }, 100);
            }
        });
    }

    async loadProviders() {
        try {
            const result = await this.rpc("/ai_chat/get_all_providers");
            if (result.success) {
                this.state.providers = result.providers;
            }
        } catch (error) {
            console.error("Error loading providers:", error);
        }
    }

    async loadMessages() {
        if (!this.state.activeAgentId) return;
        try {
            const result = await this.rpc("/ai_chat/get_messages", {
                ai_agent_id: this.state.activeAgentId,
                ai_model_id: this.state.activeModelId,
            });
            if (result.success) {
                this.state.sessionId = result.session_id;
                this.state.messages = result.messages.map(m => ({
                    ...m,
                    timestamp: new Date(m.timestamp)
                }));
                // Add initial AI message if session is new
                if (this.state.messages.length === 0) {
                     this.state.messages.push({
                        id: 'welcome',
                        type: 'ai',
                        content: `Hello! I'm ${this.state.activeAgentName || 'AI'}. How can I assist you today?`,
                        timestamp: new Date(),
                    });
                }
            }
        } catch (error) {
            console.error("Error loading messages:", error);
        }
    }

    triggerFileInput() {
        this.fileInputRef.el.click();
    }

    async onFileChange(ev) {
        const files = ev.target.files;
        if (!files) return;

        for (const file of files) {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.state.attachments.push({
                    name: file.name,
                    type: file.type,
                    data: e.target.result,
                });
            };
            reader.readAsDataURL(file);
        }
        ev.target.value = '';
    }

    removeAttachment(attach) {
        this.state.attachments = this.state.attachments.filter(a => a !== attach);
    }

    openAttachment(attach) {
        if (attach.url) {
            window.open(attach.url, '_blank');
        } else if (attach.data) {
            const win = window.open();
            win.document.write('<img src="' + attach.data + '" style="max-width:100%;" />');
        }
    }

    async sendMessage() {
        const messageInput = this.messageInputRef.el;
        const message = messageInput?.value.trim();
        if (!message && this.state.attachments.length === 0) return;

        messageInput.value = '';
        this.state.isTyping = true;

        // Add user message immediately
        const userMsg = {
            id: Date.now(),
            type: 'user',
            content: message,
            timestamp: new Date(),
            attachments: [...this.state.attachments.map(a => ({
                id: Math.random(),
                name: a.name,
                url: a.data
            }))]
        };
        this.state.messages.push(userMsg);
        this.scrollToBottom();

        try {
            const rpcParams = {
                message: message,
                ai_agent_id: this.state.activeAgentId,
                ai_model_id: this.state.activeModelId,
                session_id: this.state.sessionId,
            };

            if (this.state.attachments.length > 0) {
                rpcParams.attachments = this.state.attachments.map(a => ({
                    name: a.name,
                    data: a.data,
                }));
            }

            const result = await this.rpc("/ai_chat/send_message", rpcParams);

            if (result.success) {
                if (result.session_id) this.state.sessionId = result.session_id;

                // Replace last message with the one from server to get real attachment URLs
                const idx = this.state.messages.indexOf(userMsg);
                if (idx !== -1) {
                    this.state.messages[idx] = {
                        ...result.user_message,
                        timestamp: new Date(result.user_message.timestamp)
                    };
                }
                
                // Adding AI response
                this.state.messages.push({
                    ...result.ai_message,
                    timestamp: new Date(result.ai_message.timestamp)
                });
                
                // Clear attachments
                this.state.attachments = [];
                
                this.scrollToBottom();
            } else {
                this.notification.add(result.error || "Failed to send message", { type: "danger" });
            }
        } catch (error) {
            this.notification.add("Connection error", { type: "danger" });
        } finally {
            this.state.isTyping = false;
        }
    }


    onKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    autoResizeTextarea() {
        const textarea = this.messageInputRef.el;
        if (textarea) {
            textarea.addEventListener('input', () => {
                textarea.style.height = 'auto';
                textarea.style.height = (textarea.scrollHeight) + 'px';
            });
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            const container = this.messagesContainerRef.el;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }, 100);
    }

    toggleModelSwitcher() {
        this.state.showModelSwitcher = !this.state.showModelSwitcher;
        if (!this.state.showModelSwitcher) {
            this.state.selectedSwitcherProviderId = null;
        }
    }

    selectProvider(providerId) {
        this.state.selectedSwitcherProviderId = providerId;
    }

    backToProviders() {
        this.state.selectedSwitcherProviderId = null;
    }

    async selectModel(provider, model) {
        this.state.activeAgentId = provider.id;
        this.state.activeAgentName = provider.name;
        this.state.activeModelId = model.id;
        this.state.showModelSwitcher = false;
        
        // Save as active preference
        try {
            await this.rpc("/ai_chat/save_active_config", {
                ai_agent_id: this.state.activeAgentId,
                ai_model_id: this.state.activeModelId,
            });
        } catch (e) {
            console.error("Failed to save active config:", e);
        }

        // Reset and reload
        this.state.messages = [];
        this.state.sessionId = null;
        await this.loadMessages();
    }

    closeWindow() {
        if (this.props.onClose) {
            this.props.onClose();
        }
        if (this.props.closeChat) {
            this.props.closeChat();
        }
    }

    enlargeChat() {
        this.action.doAction("ai_chatter_screen", {
            additionalContext: {
                active_session_id: this.state.sessionId,
                ai_agent_id: this.state.activeAgentId,
                ai_model_id: this.state.activeModelId,
                ai_agent_name: this.state.activeAgentName,
            }
        });
        this.closeWindow();
    }

    formatMarkdown(content) {
        if (!content) return "";
        try {
            if (window.marked && window.hljs) {
                window.marked.setOptions({
                    highlight: function (code, lang) {
                        const language = window.hljs.getLanguage(lang) ? lang : 'plaintext';
                        return window.hljs.highlight(code, { language }).value;
                    },
                    langPrefix: 'hljs language-',
                    gfm: true,
                    breaks: true,
                });
                return markup(window.marked.parse(content));
            }
            return content;
        } catch (e) {
            return content;
        }
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

AiChatWindow.template = "ai_connector_agent.AiChatWindow";
AiChatWindow.props = {
    agentId: { type: Number, optional: true },
    agentName: { type: String, optional: true },
    modelId: { type: String, optional: true },
    onClose: { type: Function, optional: true },
    closeChat: { type: Function, optional: true },
};
