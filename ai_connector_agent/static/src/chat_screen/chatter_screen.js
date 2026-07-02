/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, onWillStart, markup } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AiChatterScreen extends Component {
    setup() {
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        this.messageInputRef = useRef("messageInput");
        this.messagesContainerRef = useRef("messagesContainer");
        this.fileInputRef = useRef("fileInput");


        this.state = useState({
            messages: [
                {
                    id: 1,
                    type: 'ai',
                    content: "Hello! I'm your AI assistant. I'm here to help you with any questions or tasks you might have. What would you like to explore together today?",
                    timestamp: new Date(),
                }
            ],
            isTyping: false,
            sidebarOpen: false,
            showSettings: false,
            sessionId: null,
            sessionName: '',
            aiAgentId: null,
            aiAgentName: '',
            aiModelId: null,
            aiModelName: '',
            sessions: { today: [], yesterday: [], last_week: [], older: [] },
            activeSessionId: null,
            attachments: [],
        });


        onWillStart(async () => {
            const context = this.props.action?.context || {};
            this.state.aiAgentId = context.ai_agent_id;
            this.state.aiModelId = context.ai_model_id;
            this.state.aiAgentName = context.ai_agent_name;
            this.state.aiModelName = context.ai_model_name;
            
            const activeSessionId = context.active_session_id;
            if (activeSessionId) {
                await this.loadSession({
                    id: activeSessionId,
                    ai_agent_id: this.state.aiAgentId,
                    ai_model_id: this.state.aiModelId,
                    ai_agent_name: this.state.aiAgentName,
                    ai_model_name: this.state.aiModelName
                });
            }
            await this.loadSessions();
        });

        onMounted(() => {
            this.setupEventListeners();
            this.autoResizeTextarea();
        });
    }

    setupEventListeners() {
        // Handle Enter key in textarea
        const messageInput = this.messageInputRef.el;
        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize textarea
            messageInput.addEventListener('input', () => {
                this.autoResizeTextarea();
            });
        }
    }
    autoResizeTextarea() {
        // Auto resize the input text area.
        const textarea = this.messageInputRef.el;
        if (textarea) {
            textarea.style.height = 'auto';
            const maxHeight = 120; // Max height in pixels
            textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + 'px';
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
                    data: e.target.result, // Base64 with prefix
                });
            };
            reader.readAsDataURL(file);
        }
        // Reset input value to allow selecting same file again
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
        // If there is no user query return none
        if (!message) return;
        // If there is no ai model or ai agent, show the notification
        if (!this.state.aiAgentId || !this.state.aiModelId) {
            this.notification.add("AI configuration is missing", {
                type: "danger",
            });
            return;
        }

        // Clear input
        messageInput.value = '';
        this.autoResizeTextarea();

        // Show typing indicator
        this.state.isTyping = true;

        // Sending user messages.
        try {
            const rpcParams = {
                message: message,
                ai_agent_id: this.state.aiAgentId,
                ai_model_id: this.state.aiModelId,
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
                // Update session ID if new
                if (result.session_id && !this.state.sessionId) {
                    this.state.sessionId = result.session_id;
                }

                // Add user message
                this.state.messages.push({
                    ...result.user_message,
                    timestamp: new Date(result.user_message.timestamp)
                });

                // Add AI response
                this.state.messages.push({
                    ...result.ai_message,
                    timestamp: new Date(result.ai_message.timestamp)
                });

                // Clear attachments
                this.state.attachments = [];

                this.scrollToBottom();

            } else {
                this.notification.add(result.error || "Failed to send message", {
                    type: "danger",
                });
            }
        } catch (error) {
            console.error("Error sending message:", error);
            this.notification.add("Failed to send message. Please try again.", {
                type: "danger",
            });
        } finally {
            this.state.isTyping = false;
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

    formatTime(timestamp) {
        if (!timestamp) return '';
        return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    formatMarkdown(content) {
        if (!content) return "";
        try {
            if (window.marked && window.hljs) {
                // Configure marked to use highlight.js if not already configured
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
            } else {
                // Fallback if libraries are not fully loaded yet
                return content;
            }
        } catch (e) {
            console.error("Markdown parsing error", e);
            return content;
        }
    }

    toggleSidebar() {
        this.state.sidebarOpen = !this.state.sidebarOpen;
    }

    toggleSettings() {
        this.state.showSettings = !this.state.showSettings;
    }

    async loadSessions() {
        try {
            const result = await this.rpc('/ai_chat/get_sessions', {});
            if (result.success) {
                this.state.sessions = result.sessions;
            }
        } catch (e) {
            console.error('Failed to load sessions:', e);
        }
    }

    async loadSession(session) {
        this.state.showSettings = false;
        this.state.activeSessionId = session.id;
        this.state.sessionId = session.id;
        this.state.aiAgentId = session.ai_agent_id;
        this.state.aiModelId = session.ai_model_id;
        this.state.aiAgentName = session.ai_agent_name || session.name;
        this.state.aiModelName = session.ai_model_name || session.model_name;

        try {
            const result = await this.rpc('/ai_chat/get_messages', {
                ai_agent_id: session.ai_agent_id,
                ai_model_id: session.ai_model_id,
                session_id: session.id,
            });
            if (result.success) {
                this.state.messages = result.messages.map(m => ({
                    ...m,
                    timestamp: new Date(m.timestamp),
                }));
                if (this.state.messages.length === 0) {
                    this.state.messages = [{
                        id: 'welcome',
                        type: 'ai',
                        content: `Hello! How can I help you today?`,
                        timestamp: new Date(),
                    }];
                }
                this.scrollToBottom();
            }
        } catch (e) {
            console.error('Failed to load session messages:', e);
        }
    }

    async newChat() {
        this.state.messages = [{
            id: 'welcome',
            type: 'ai',
            content: `Hello! I'm ${this.state.aiAgentName || 'your AI assistant'}. How can I help you today?`,
            timestamp: new Date(),
        }];
        this.state.sessionId = null;
        this.state.activeSessionId = null;
        this.state.isTyping = false;
        this.state.showSettings = false;
        await this.loadSessions();
    }

    async clearChat() {
        if (this.state.sessionId) {
            try {
                const result = await this.rpc('/ai_chat/delete_session', {
                    session_id: this.state.sessionId
                });
                if (result.success) {
                    await this.loadSessions();
                }
            } catch (e) {
                console.error('Failed to delete session:', e);
            }
        }
        this.state.showSettings = false;
        this.newChat();
    }

    goBack() {
        this.state.showSettings = false;
        return this.actionService.doAction("ai_chatter_home", {
            clear_breadcrumbs: true,
            additionalContext: {
                skip_redirect: true,
            }
        });
    }
}

AiChatterScreen.template = "ai_connector_agent.ai_chatter_screen";
registry.category("actions").add("ai_chatter_screen", AiChatterScreen);
