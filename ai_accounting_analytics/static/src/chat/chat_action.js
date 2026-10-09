import { Component, onMounted, onWillStart, proxy, signal, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { deserializeDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { formatFloat, formatInteger } from "@web/views/fields/formatters";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

import { streamChat } from "./chat_stream";
import { AiChatMessage } from "./chat_message";

const { DateTime } = luxon;

const SUGGESTIONS = [
    {
        icon: "receipt_long",
        title: _t("Profit & Loss"),
        prompt: _t("Show the profit and loss for this month"),
    },
    {
        icon: "group",
        title: _t("Top customers"),
        prompt: _t("Top 10 customers this year"),
    },
    {
        icon: "speed",
        title: _t("Health check"),
        prompt: _t("How are we doing this quarter compared to last quarter?"),
    },
    {
        icon: "schedule",
        title: _t("Overdue invoices"),
        prompt: _t("Which customer invoices are overdue?"),
    },
    {
        icon: "bar_chart",
        title: _t("Revenue trend"),
        prompt: _t("Revenue trend for the last 12 months as a chart"),
    },
    {
        icon: "account_balance",
        title: _t("Cash position"),
        prompt: _t("What is our cash and bank position today?"),
    },
];

export class AiAnalyticsChat extends Component {
    static template = "ai_accounting_analytics.Chat";
    static components = { AiChatMessage };
    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.suggestions = SUGGESTIONS;
        this.scrollRef = signal.ref();
        this.inputRef = signal.ref();
        this.userAvatar = `/web/image/res.users/${user.userId}/avatar_128`;
        this.state = proxy({
            loaded: false,
            consent: false,
            models: [],
            modelId: false,
            chats: [],
            chatId: false,
            messages: [],
            input: "",
            search: "",
            streaming: false,
            renamingId: false,
            renameValue: "",
            userName: "",
            usage: { tokens: 0, cost: 0 },
        });
        this.abortController = null;

        onWillStart(async () => {
            const data = await this.orm.call("ai.accounting.chat", "ai_get_bootstrap", []);
            Object.assign(this.state, {
                loaded: true,
                consent: data.consent,
                models: data.models,
                modelId: data.default_model_id,
                chats: data.chats,
                userName: data.user_name,
                usage: data.usage,
            });
            // Opened on a given conversation (e.g. from the usage dashboard).
            const chatId = this.props.action.context?.ai_chat_id;
            if (chatId && data.chats.some((chat) => chat.id === chatId)) {
                await this.openChat(chatId);
            }
        });
        onMounted(() => this.inputRef()?.focus());
    }

    // ------------------------------------------------------------------
    // Display helpers
    // ------------------------------------------------------------------
    currentModel() {
        return this.state.models.find((model) => model.id === this.state.modelId);
    }

    chatTitle() {
        const chat = this.state.chats.find((item) => item.id === this.state.chatId);
        return chat ? chat.name : _t("New conversation");
    }

    greeting() {
        const hour = new Date().getHours();
        const name = this.state.userName;
        if (hour < 12) {
            return name ? _t("Good morning, %s", name) : _t("Good morning");
        }
        if (hour < 18) {
            return name ? _t("Good afternoon, %s", name) : _t("Good afternoon");
        }
        return name ? _t("Good evening, %s", name) : _t("Good evening");
    }

    usageLabel() {
        const { tokens, cost } = this.state.usage;
        return _t("%(tokens)s tokens · $%(cost)s", {
            tokens: formatInteger(tokens || 0),
            cost: formatFloat(cost || 0, { digits: [16, 2] }),
        });
    }

    /** Conversations grouped by recency, filtered by the search box. */
    chatGroups() {
        const search = this.state.search.trim().toLowerCase();
        const today = DateTime.now().startOf("day");
        const groups = [
            { key: "today", label: _t("Today"), chats: [] },
            { key: "yesterday", label: _t("Yesterday"), chats: [] },
            { key: "week", label: _t("Previous 7 days"), chats: [] },
            { key: "older", label: _t("Older"), chats: [] },
        ];
        for (const chat of this.state.chats) {
            if (search && !chat.name.toLowerCase().includes(search)) {
                continue;
            }
            const date = chat.date ? deserializeDateTime(chat.date).startOf("day") : today;
            const days = Math.round(today.diff(date, "days").days);
            const index = days <= 0 ? 0 : days === 1 ? 1 : days <= 7 ? 2 : 3;
            groups[index].chats.push(chat);
        }
        return groups.filter((group) => group.chats.length);
    }

    isLastAssistant(message) {
        const messages = this.state.messages;
        return message === messages[messages.length - 1] && message.role === "assistant";
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            const el = this.scrollRef();
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        });
    }

    // ------------------------------------------------------------------
    // Conversations
    // ------------------------------------------------------------------
    newChat() {
        if (this.state.streaming) {
            return;
        }
        this.state.chatId = false;
        this.state.messages = [];
        this.inputRef()?.focus();
    }

    async openChat(chatId) {
        if (this.state.streaming || this.state.renamingId || chatId === this.state.chatId) {
            return;
        }
        const messages = await this.orm.call("ai.accounting.chat", "ai_get_messages", [[chatId]]);
        this.state.chatId = chatId;
        this.state.messages = messages;
        this.scrollToBottom();
    }

    startRename(chat) {
        this.state.renamingId = chat.id;
        this.state.renameValue = chat.name;
    }

    onRenameInput(ev) {
        this.state.renameValue = ev.target.value;
    }

    async confirmRename(chat) {
        if (this.state.renamingId !== chat.id) {
            return;
        }
        const name = this.state.renameValue.trim();
        this.state.renamingId = false;
        if (name && name !== chat.name) {
            await this.orm.write("ai.accounting.chat", [chat.id], { name });
            chat.name = name;
        }
    }

    onRenameKeydown(ev, chat) {
        if (ev.key === "Enter") {
            this.confirmRename(chat);
        } else if (ev.key === "Escape") {
            this.state.renamingId = false;
        }
    }

    async deleteChat(chat) {
        if (this.state.streaming) {
            return;
        }
        await this.orm.unlink("ai.accounting.chat", [chat.id]);
        this.state.chats = this.state.chats.filter((item) => item.id !== chat.id);
        if (this.state.chatId === chat.id) {
            this.newChat();
        }
    }

    onSearchInput(ev) {
        this.state.search = ev.target.value;
    }

    // ------------------------------------------------------------------
    // Consent & configuration
    // ------------------------------------------------------------------
    async acceptConsent() {
        await this.orm.call("ai.accounting.chat", "ai_accept_consent", []);
        this.state.consent = true;
    }

    openApiKeys() {
        this.actionService.doAction("ai_accounting_analytics.ai_accounting_api_key_action");
    }

    openUsage() {
        this.actionService.doAction("ai_accounting_analytics.ai_accounting_usage_dashboard_action");
    }

    onModelChange(ev) {
        this.state.modelId = parseInt(ev.target.value);
    }

    // ------------------------------------------------------------------
    // Composer
    // ------------------------------------------------------------------
    onInput(ev) {
        this.state.input = ev.target.value;
        ev.target.style.height = "auto";
        ev.target.style.height = `${Math.min(ev.target.scrollHeight, 200)}px`;
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey && !ev.isComposing) {
            ev.preventDefault();
            this.send();
        }
    }

    useSuggestion(suggestion) {
        this.state.input = suggestion.prompt;
        this.send();
    }

    /** Ask again the question that produced ``message`` (failed answers). */
    retry(message) {
        const index = this.state.messages.indexOf(message);
        const question = this.state.messages
            .slice(0, index)
            .reverse()
            .find((item) => item.role === "user");
        if (question && !this.state.streaming) {
            this.state.input = question.content;
            this.send();
        }
    }

    stop() {
        this.abortController?.abort();
    }

    async send() {
        const question = this.state.input.trim();
        if (!question || this.state.streaming || !this.state.consent) {
            return;
        }
        this.state.input = "";
        const input = this.inputRef();
        if (input) {
            input.style.height = "auto";
        }
        this.state.messages.push({ id: `user-${Date.now()}`, role: "user", content: question });
        this.state.messages.push({
            id: `pending-${Date.now()}`,
            role: "assistant",
            content: "",
            parts: [],
            steps: [],
            pending: true,
        });
        // Work on the reactive proxy so every change re-renders.
        const answer = this.state.messages[this.state.messages.length - 1];
        const started = Date.now();
        this.state.streaming = true;
        this.abortController = new AbortController();
        this.scrollToBottom();
        try {
            const events = streamChat(
                {
                    question,
                    chat_id: this.state.chatId,
                    model_id: this.state.modelId,
                    company_ids: (user.context.allowed_company_ids || []).join(","),
                },
                this.abortController.signal
            );
            for await (const event of events) {
                this.handleEvent(event, answer, started);
            }
        } catch (error) {
            if (error.name !== "AbortError") {
                answer.parts.push({ type: "error", text: _t("Connection lost: %s", error.message) });
            } else {
                answer.parts.push({ type: "error", text: _t("Stopped.") });
            }
        } finally {
            answer.pending = false;
            answer.notice = false;
            answer.duration_ms = answer.duration_ms || Date.now() - started;
            this.state.streaming = false;
            this.abortController = null;
            this.scrollToBottom();
        }
    }

    handleEvent(event, answer, started) {
        if (event.type === "ping") {
            // Keep-alive sent while the AI provider is silent.
            return;
        }
        switch (event.type) {
            case "start":
                this.state.chatId = event.chat.id;
                if (!this.state.chats.some((chat) => chat.id === event.chat.id)) {
                    this.state.chats.unshift({ ...event.chat, date: false });
                }
                break;
            case "retry":
                answer.notice = event.message;
                break;
            case "rewind":
                answer.parts = event.parts;
                answer.content = event.parts
                    .filter((part) => part.type === "text")
                    .map((part) => part.text)
                    .join("");
                break;
            case "delta": {
                const last = answer.parts[answer.parts.length - 1];
                if (last && last.type === "text") {
                    last.text += event.text;
                } else {
                    answer.parts.push({ type: "text", text: event.text });
                }
                answer.content += event.text;
                answer.notice = false;
                break;
            }
            case "step":
                if (event.status === "running") {
                    answer.steps.push({ label: event.label, running: true });
                } else {
                    answer.steps[event.index] = event;
                }
                answer.duration_ms = Date.now() - started;
                break;
            case "block":
                answer.parts.push(event.block);
                answer.notice = false;
                break;
            case "usage":
                answer.input_tokens = event.input_tokens;
                answer.output_tokens = event.output_tokens;
                answer.cost = event.cost;
                break;
            case "error":
                answer.parts.push({ type: "error", text: event.message });
                answer.notice = false;
                break;
            case "done": {
                Object.assign(answer, event.message, { pending: false, notice: false });
                this.state.usage.tokens += (answer.input_tokens || 0) + (answer.output_tokens || 0);
                this.state.usage.cost += answer.cost || 0;
                const chat = this.state.chats.find((item) => item.id === event.chat.id);
                if (chat) {
                    chat.date = event.chat.date;
                }
                break;
            }
        }
        this.scrollToBottom();
    }

    // ------------------------------------------------------------------
    // Message actions
    // ------------------------------------------------------------------
    async exportBlock(messageId, index, format) {
        const action = await this.orm.call("ai.accounting.chat", "ai_export", [
            [this.state.chatId],
            messageId,
            index,
            format,
        ]);
        if (action) {
            await this.actionService.doAction(action);
        }
    }

    openRecord(resModel, resId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: resModel,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("ai_accounting_analytics.chat", AiAnalyticsChat);
