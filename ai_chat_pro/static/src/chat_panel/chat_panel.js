import { browser } from "@web/core/browser/browser";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { deserializeDate, deserializeDateTime, formatDate } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { download, downloadFile } from "@web/core/network/download";
import { RPCError } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onPatched, onWillStart, onWillUnmount, proxy, signal, t, useProps } from "@odoo/owl";
import { AiChatChart } from "../chat_chart/chat_chart";
import { NextStepActivityDialog } from "../next_step_dialog/next_step_dialog";
import { canRecordVoice, toVoiceAudio, VoiceRecorder } from "../voice/voice_recorder";

const CONVERSATION_MODEL = "ai.chat.conversation";
const LAST_CONVERSATION_KEY = "ai_chat_pro.last_conversation_id";
// folded parts of the sidebar, remembered per browser
const SIDEBAR_COLLAPSED_KEY = "ai_chat_pro.sidebar_collapsed";
// the usage and cost under the user, in the sidebar: closed unless opened
const USAGE_OPEN_KEY = "ai_chat_pro.usage_open";
const DEEP_ANALYSIS_KEY = "ai_chat_pro.deep_analysis";
// files a question can come with: spreadsheets (imported), documents and pictures of documents
// (a record is created from them)
const SPREADSHEET_EXTENSIONS = ["csv", "xlsx", "xls", "ods"];
const DOCUMENT_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "webp"];
const ATTACHMENT_EXTENSIONS = [...SPREADSHEET_EXTENSIONS, ...DOCUMENT_EXTENSIONS];
const MAX_ATTACHMENTS = 3;
const MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024;
// "@" mentions a record: the text typed after it, before the cursor, is searched
const MENTION_TRIGGER = /(^|\s)@([^\s@]{0,40}(?: [^\s@]{1,40}){0,3})$/;
const MENTION_SEARCH_DELAY = 220;
// "/" starts a command, at the start of a word: the name typed after it, before the cursor, filters them
const COMMAND_TRIGGER = /(^|\s)\/([a-z_]{0,20})$/i;
const COMMAND_RE = /(^|\s)(\/[a-z_]+)(?=\s|$)/gi;
// activities of a record explained, by state
const ACTIVITY_STATES = {
    overdue: { label: "Overdue", icon: "error" },
    today: { label: "Today", icon: "schedule" },
    planned: { label: "Planned", icon: "calendar_today" },
    done: { label: "Done", icon: "check" },
};
// icons of the records mentioned, by model
const MENTION_ICONS = {
    "res.partner": "person",
    "product.template": "deployed_code",
    "sale.order": "shopping_bag",
    "purchase.order": "shopping_cart",
    "account.move": "description",
    "crm.lead": "handshake",
    "project.project": "folder",
    "project.task": "checklist",
    "hr.employee": "badge",
    "stock.picking": "local_shipping",
    "res.users": "account_circle",
    "calendar.event": "calendar_today",
};
// below this width the sidebar is a drawer (Bootstrap's lg breakpoint, as in the styles)
const DRAWER_MEDIA_QUERY = "(max-width: 991.98px)";
// the keys of the questions of the voice assistant already asked, in this tab
const ASKED_VOICE_QUESTIONS = new Set();

// what the assistant can do, shown on the landing page: a click puts the request in the composer to complete
// ("fill"), asks it ("ask"), opens the file picker ("attach") or turns on the deep analysis ("deep")
export const AI_CHAT_CAPABILITIES = [
    {
        key: "insights", icon: "bar_chart", title: _t("Insights & charts"),
        description: _t("Totals, top lists, trends and charts of your data, in plain words"),
        action: "ask", text: _t("Totals per month this year"),
    },
    {
        key: "create", icon: "add_box", title: _t("Create records"),
        description: _t("Sales orders, contacts, invoices... drafted for you to confirm"),
        action: "fill", text: _t("Create a "),
    },
    {
        key: "deep", icon: "lightbulb", title: _t("Deep analysis"),
        description: _t("Decisions with reasons and next steps, planned as activities"),
        action: "deep",
    },
    {
        key: "files", icon: "attach_file", title: _t("Import & read files"),
        description: _t("Records from a spreadsheet, or a bill from a PDF or a photo"),
        action: "attach",
    },
    {
        key: "export", icon: "download", title: _t("PDF & Excel exports"),
        description: _t("Download any answer as a PDF report or an XLSX file"),
        action: "ask", text: _t("List the 10 latest records"),
    },
    {
        key: "mention", icon: "alternate_email", title: _t("Mention records"),
        description: _t("@ points to the very record you mean: a customer, an order..."),
        action: "fill", text: "@",
    },
    {
        key: "explain", icon: "search", title: "/explain",
        description: _t("A detailed summary of a record, with its history and activities"),
        action: "fill", text: "/explain @",
    },
    {
        key: "report", icon: "print", title: "/report",
        description: _t("Print the Odoo report of a record: a quotation, an invoice..."),
        action: "fill", text: "/report @",
    },
];

// what a deep analysis is doing, shown in turn while it runs
const DEEP_STEPS = [
    _t("Planning the analysis"),
    _t("Reading your data"),
    _t("Comparing the figures"),
    _t("Weighing the options"),
    _t("Writing the recommendation"),
];
const DEEP_STEP_MS = 2600;

// the charts a table answer can be switched to; pie charts draw a single value
export const CHART_TYPES = [
    { type: "bar", icon: "bar_chart", label: _t("Bar chart") },
    { type: "line", icon: "show_chart", label: _t("Line chart") },
    { type: "pie", icon: "pie_chart", label: _t("Pie chart") },
];

// answers that make a PDF report: those with data
const REPORT_RESULT_TYPES = ["table", "value"];

/**
 * Post values to a URL in a browser tab, as a form does.
 */
function postInTab(url, values, target) {
    const form = document.createElement("form");
    Object.assign(form, { method: "POST", action: url, target });
    for (const [name, value] of Object.entries({ ...values, csrf_token: odoo.csrf_token })) {
        const input = document.createElement("input");
        Object.assign(input, { type: "hidden", name, value });
        form.append(input);
    }
    document.body.append(form);
    form.submit();
    form.remove();
}

function blobToDataUrl(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
    });
}

const SOURCE_LABELS = {
    local: _t("No AI call"),
    cache: _t("From cache"),
    openrouter: _t("AI decision"),
    openrouter_olg: _t("AI decision + Odoo AI"),
    cache_olg: _t("Cache + Odoo AI"),
    olg: _t("Odoo AI"),
    deep: _t("Deep analysis · Odoo AI"),
};
// answers of former versions only tell their source: what it says of the AI used
const DECISION_SOURCES = ["openrouter", "openrouter_olg"];
const CACHE_SOURCES = ["cache", "cache_olg"];
const OLG_SOURCES = ["openrouter_olg", "cache_olg", "olg"];

/**
 * Chat with the AI assistant. Used full screen by the client action, with the list
 * of the conversations and the usage of the assistant in a sidebar, and compact in
 * the chat window of the systray. Conversations are stored on the server, so both
 * show the same conversations.
 */
export class AiChatPanel extends Component {
    static template = "ai_chat_pro.ChatPanel";
    static components = { AiChatChart };
    props = useProps({
        compact: t.boolean().optional(false),
        onExpand: t.function().optional(),
        onClose: t.function().optional(),
        // a question asked to the voice assistant of the systray: { key, text }
        voiceQuestion: t.object().optional(),
        // the conversation to open, rather than the last one
        conversationId: t.or([t.number(), t.boolean()]).optional(),
    });

    setup() {
        this.chartTypes = CHART_TYPES;
        this.messagesRef = signal.ref();
        this.inputRef = signal.ref();
        this.fileInputRef = signal.ref();
        this.attachmentAccept = ATTACHMENT_EXTENSIONS.map((extension) => `.${extension}`).join(",");
        this.userName = user.name;
        this.userAvatar = `/web/image/res.users/${user.userId}/avatar_128`;
        // with the minimal theme, the full screen title is the navbar heading like
        // on its other screens; the theme is optional, so it is detected rather
        // than depended on
        this.usesNavbarHeading =
            !this.props.compact && odoo.loader.modules.has("@ai_minimal_theme/webclient/webclient_patch");
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.notification = useService("notification");
        this.state = proxy({
            conversations: [],
            conversationId: false,
            conversationName: "",
            messages: [],
            usage: false,
            question: "",
            search: "",
            isAsking: false,
            isLoading: true,
            isRefreshingBalance: false,
            // on small screens, the sidebar is a drawer
            isSidebarOpen: false,
            // on large screens, the sidebar can be folded away to the left, and its usage card folded
            isSidebarCollapsed: browser.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1",
            isUsageCollapsed: browser.localStorage.getItem(USAGE_OPEN_KEY) !== "1",
            // deep analysis: enabled in the settings, turned on by the user, and the step shown
            // while an analysis runs
            deepAvailable: false,
            // example questions on the data of the user's apps, by capability
            examples: {},
            isDeep: browser.localStorage.getItem(DEEP_ANALYSIS_KEY) === "1",
            deepStep: 0,
            isAskingDeep: false,
            // files sent with the next question, and those being uploaded
            attachments: [],
            uploadingFiles: [],
            isDragging: false,
            // "@": the records offered for the text typed after it, and those mentioned in the question
            mention: { open: false, term: "", start: 0, results: [], index: 0, loading: false },
            mentions: [],
            // the use case of the landing page pointed at, described under them
            capabilityHint: false,
            // "/": the commands of the chat, and those offered for the text typed after it
            commands: [],
            command: { open: false, term: "", start: 0, results: [], index: 0 },
            // per answer: shown as a chart or a table, and the chart type the user picked
            resultViews: {},
            chartTypes: {},
            // voice questions: enabled in the settings, being recorded, being turned into text
            voice: false,
            isRecording: false,
            isTranscribing: false,
            recordingSeconds: 0,
            // the draft answer whose record is being created or discarded
            pendingDraftId: false,
            // the answer whose PDF report is being printed
            printingReportId: false,
            // whether the server prints PDF reports, else the browser does
            pdfEngine: true,
        });
        this.canRecord = canRecordVoice();
        this.recorder = null;
        this.shouldScroll = true;
        // per answer, the function exporting its chart as an image
        this.chartExports = {};
        // a question asked to the voice assistant opens a new chat, once: coming back to the
        // chat with the breadcrumbs shows its conversation instead of asking it again
        const voiceQuestion = this.props.voiceQuestion;
        this.pendingQuestion = voiceQuestion && !ASKED_VOICE_QUESTIONS.has(voiceQuestion.key) && voiceQuestion.text;
        if (this.pendingQuestion) {
            ASKED_VOICE_QUESTIONS.add(voiceQuestion.key);
        }
        onWillStart(() => {
            const lastId = parseInt(browser.localStorage.getItem(LAST_CONVERSATION_KEY), 10) || false;
            return this.loadConversation(this.pendingQuestion ? false : this.props.conversationId || lastId);
        });
        onMounted(() => {
            this.afterRender();
            if (this.pendingQuestion) {
                this.state.question = this.pendingQuestion;
                this.pendingQuestion = false;
                this.ask();
            }
        });
        onPatched(() => this.afterRender());
        onWillUnmount(() => {
            this.cancelRecording();
            browser.clearInterval(this.deepInterval);
        });
    }

    afterRender() {
        const messages = this.messagesRef();
        if (this.shouldScroll && messages) {
            messages.scrollTop = messages.scrollHeight;
            this.shouldScroll = false;
        }
        const input = this.inputRef();
        if (this.focusInput && !this.state.isAsking && input) {
            input.focus();
            this.focusInput = false;
        }
    }

    // Conversations ------------------------------------------------------------

    async loadConversation(conversationId) {
        this.state.isLoading = true;
        try {
            const data = await this.orm.call(CONVERSATION_MODEL, "get_chat_data", [conversationId]);
            this.state.conversations = data.conversations;
            this.state.usage = data.usage;
            this.state.voice = data.voice;
            this.state.deepAvailable = Boolean(data.deep_analysis);
            this.state.examples = data.examples || {};
            this.state.pdfEngine = data.pdf_engine;
            this.state.commands = data.commands || [];
            this.setConversation(data.conversation);
        } finally {
            this.state.isLoading = false;
        }
    }

    setConversation(conversation) {
        this.state.conversationId = conversation ? conversation.id : false;
        this.state.conversationName = conversation ? conversation.name : "";
        this.state.messages = conversation ? conversation.messages : [];
        this.shouldScroll = true;
        this.focusInput = true;
        if (conversation) {
            browser.localStorage.setItem(LAST_CONVERSATION_KEY, conversation.id);
        } else {
            browser.localStorage.removeItem(LAST_CONVERSATION_KEY);
        }
    }

    newConversation() {
        this.setConversation(false);
        this.state.question = "";
        this.state.isSidebarOpen = false;
    }

    selectConversation(conversationId) {
        this.state.isSidebarOpen = false;
        if (conversationId !== this.state.conversationId) {
            this.loadConversation(conversationId);
        }
    }

    toggleSidebar() {
        if (this.state.isSidebarCollapsed && !this.isDrawerScreen()) {
            this.setSidebarCollapsed(false);
        } else {
            this.state.isSidebarOpen = !this.state.isSidebarOpen;
        }
    }

    /**
     * Hide the sidebar: the drawer is closed on small screens, the sidebar is folded
     * away to the left on large ones.
     */
    collapseSidebar() {
        if (this.state.isSidebarOpen) {
            this.state.isSidebarOpen = false;
        } else {
            this.setSidebarCollapsed(true);
        }
    }

    setSidebarCollapsed(collapsed) {
        this.state.isSidebarCollapsed = collapsed;
        browser.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
    }

    toggleUsage() {
        this.state.isUsageCollapsed = !this.state.isUsageCollapsed;
        browser.localStorage.setItem(USAGE_OPEN_KEY, this.state.isUsageCollapsed ? "0" : "1");
    }

    get usageToggleTitle() {
        return this.state.isUsageCollapsed ? _t("Show usage and cost") : _t("Hide usage and cost");
    }

    isDrawerScreen() {
        return browser.matchMedia(DRAWER_MEDIA_QUERY).matches;
    }

    /**
     * Whether the button showing the sidebar is shown: always on small screens (the
     * styles hide it on large ones), and on large ones when the sidebar is folded.
     */
    get showsSidebarToggle() {
        return this.state.isSidebarCollapsed;
    }

    onPanelKeydown(ev) {
        if (ev.key === "Escape" && this.state.isRecording) {
            ev.stopPropagation();
            this.cancelRecording();
        } else if (ev.key === "Escape" && this.state.isSidebarOpen) {
            ev.stopPropagation();
            this.state.isSidebarOpen = false;
        }
    }

    deleteConversation(conversation) {
        this.dialogService.add(ConfirmationDialog, {
            title: _t("Delete conversation"),
            body: _t('Delete the conversation "%s"?', conversation.name),
            confirmLabel: _t("Delete"),
            confirm: async () => {
                await this.orm.unlink(CONVERSATION_MODEL, [conversation.id]);
                const isCurrent = conversation.id === this.state.conversationId;
                await this.loadConversation(isCurrent ? false : this.state.conversationId);
            },
            cancel: () => {},
        });
    }

    onSearchInput(ev) {
        this.state.search = ev.target.value;
    }

    /**
     * The conversations matching the search, grouped by when they were last used.
     */
    get conversationGroups() {
        const search = this.state.search.trim().toLowerCase();
        const today = luxon.DateTime.local().startOf("day");
        const sections = [
            { key: "today", label: _t("Today"), from: today, conversations: [] },
            { key: "yesterday", label: _t("Yesterday"), from: today.minus({ days: 1 }), conversations: [] },
            { key: "week", label: _t("Previous 7 days"), from: today.minus({ days: 7 }), conversations: [] },
            { key: "older", label: _t("Older"), from: null, conversations: [] },
        ];
        for (const conversation of this.state.conversations) {
            if (search && !conversation.name.toLowerCase().includes(search)) {
                continue;
            }
            const date = conversation.date ? deserializeDateTime(conversation.date) : null;
            const section = sections.find((s) => !s.from || (date && date >= s.from));
            section.conversations.push(conversation);
        }
        return sections.filter((section) => section.conversations.length);
    }

    // Questions ----------------------------------------------------------------

    onInput(ev) {
        this.state.question = ev.target.value;
        this.updateMention(ev.target);
        this.updateCommand(ev.target);
    }

    onKeydown(ev) {
        const command = this.state.command;
        if (command.open && command.results.length) {
            if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
                ev.preventDefault();
                const step = ev.key === "ArrowDown" ? 1 : -1;
                command.index = (command.index + step + command.results.length) % command.results.length;
                return;
            }
            if (ev.key === "Enter" || ev.key === "Tab") {
                ev.preventDefault();
                this.selectCommand(command.results[command.index]);
                return;
            }
        }
        if (command.open && ev.key === "Escape") {
            ev.preventDefault();
            ev.stopPropagation();
            this.closeCommand();
            return;
        }
        const mention = this.state.mention;
        if (mention.open && mention.results.length) {
            if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
                ev.preventDefault();
                const step = ev.key === "ArrowDown" ? 1 : -1;
                mention.index = (mention.index + step + mention.results.length) % mention.results.length;
                return;
            }
            if (ev.key === "Enter" || ev.key === "Tab") {
                ev.preventDefault();
                this.selectMention(mention.results[mention.index]);
                return;
            }
        }
        if (mention.open && ev.key === "Escape") {
            ev.preventDefault();
            ev.stopPropagation();
            this.closeMention();
            return;
        }
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.ask();
        }
    }

    // Records mentioned with "@" ------------------------------------------------------

    /**
     * Open, update or close the records offered for "@", from the text before the cursor.
     */
    updateMention(input) {
        const before = input.value.slice(0, input.selectionStart ?? input.value.length);
        const match = before.match(MENTION_TRIGGER);
        if (!match) {
            this.closeMention();
            return;
        }
        const term = match[2];
        const mention = this.state.mention;
        Object.assign(mention, { open: true, term, start: before.length - term.length - 1 });
        browser.clearTimeout(this.mentionTimer);
        if (!term.trim()) {
            Object.assign(mention, { results: [], loading: false });
            return;
        }
        mention.loading = true;
        const searched = term;
        this.mentionTimer = browser.setTimeout(async () => {
            let results = [];
            try {
                results = await this.orm.call(CONVERSATION_MODEL, "search_mentions", [searched]);
            } catch {
                results = [];
            }
            // only the answer to the text typed last
            if (this.state.mention.term === searched) {
                Object.assign(this.state.mention, { results, index: 0, loading: false });
            }
        }, MENTION_SEARCH_DELAY);
    }

    closeMention() {
        browser.clearTimeout(this.mentionTimer);
        Object.assign(this.state.mention, { open: false, term: "", results: [], index: 0, loading: false });
    }

    selectMention(record) {
        if (!record) {
            return;
        }
        const { start, term } = this.state.mention;
        const text = this.state.question;
        const inserted = `@${record.name} `;
        this.state.question = text.slice(0, start) + inserted + text.slice(start + term.length + 1);
        if (!this.state.mentions.some((m) => m.model === record.model && m.id === record.id)) {
            this.state.mentions.push(record);
        }
        this.closeMention();
        const caret = start + inserted.length;
        browser.setTimeout(() => {
            const input = this.inputRef();
            if (input) {
                input.value = this.state.question;
                input.focus();
                input.setSelectionRange(caret, caret);
            }
        }, 0);
    }

    // Commands typed after "/" ----------------------------------------------------------

    /**
     * Open, update or close the commands offered for "/", from the text before the cursor.
     */
    updateCommand(input) {
        const before = input.value.slice(0, input.selectionStart ?? input.value.length);
        const match = this.state.commands.length && before.match(COMMAND_TRIGGER);
        if (!match) {
            this.closeCommand();
            return;
        }
        const term = match[2].toLowerCase();
        const results = this.state.commands.filter((command) => command.name.startsWith(term));
        Object.assign(this.state.command, {
            open: true,
            term,
            start: before.length - term.length - 1,
            results,
            index: Math.min(this.state.command.index, Math.max(results.length - 1, 0)),
        });
    }

    closeCommand() {
        Object.assign(this.state.command, { open: false, term: "", results: [], index: 0 });
    }

    selectCommand(command) {
        if (!command) {
            return;
        }
        const { start, term } = this.state.command;
        const text = this.state.question;
        // the command, then "@" to mention the record it is about
        const inserted = `/${command.name} @`;
        const after = text.slice(start + term.length + 1).replace(/^\s+/, "");
        this.state.question = text.slice(0, start) + inserted + after;
        this.closeCommand();
        const caret = start + inserted.length;
        browser.setTimeout(() => {
            const input = this.inputRef();
            if (input) {
                input.value = this.state.question;
                input.focus();
                input.setSelectionRange(caret, caret);
                this.updateMention(input);
            }
        }, 0);
    }

    getMentionIcon(record) {
        return MENTION_ICONS[record.model] || "article";
    }

    /**
     * The text of a question, with the records it mentions as parts of their own.
     */
    getMessageParts(message) {
        const mentions = message.mentions || [];
        if (!mentions.length) {
            return this.getCommandParts(message.content);
        }
        const escape = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const names = [...mentions].sort((a, b) => b.name.length - a.name.length);
        const pattern = new RegExp(`@(${names.map((m) => escape(m.name)).join("|")})`, "g");
        const parts = [];
        let last = 0;
        for (const match of message.content.matchAll(pattern)) {
            if (match.index > last) {
                parts.push(...this.getCommandParts(message.content.slice(last, match.index)));
            }
            parts.push({ mention: names.find((m) => m.name === match[1]) });
            last = match.index + match[0].length;
        }
        if (last < message.content.length) {
            parts.push(...this.getCommandParts(message.content.slice(last)));
        }
        return parts;
    }

    /**
     * A text, with the commands it holds ("/explain") as parts of their own.
     */
    getCommandParts(text) {
        const names = new Set(this.state.commands.map((command) => `/${command.name}`));
        const parts = [];
        let last = 0;
        for (const match of text.matchAll(COMMAND_RE)) {
            if (!names.has(match[2].toLowerCase())) {
                continue;
            }
            const start = match.index + match[1].length;
            if (start > last) {
                parts.push({ text: text.slice(last, start) });
            }
            parts.push({ command: match[2] });
            last = start + match[2].length;
        }
        if (last < text.length || !parts.length) {
            parts.push({ text: text.slice(last) });
        }
        return parts;
    }

    isExplanation(message) {
        return message.result?.type === "explain";
    }

    isPrint(message) {
        return message.result?.type === "print";
    }

    /**
     * The URL printing a report of a record: a PDF when the server prints them, else the
     * page of the report, opening the print window of the browser.
     */
    getRecordReportUrl(result, reportId) {
        return `/ai_chat_pro/record_report/${reportId}/${result.model}/${result.id}`;
    }

    getPrintedFileUrl(result, download = false) {
        return `/web/content/${result.attachment_id}${download ? "?download=true" : ""}`;
    }

    openRecordReport(result, reportId) {
        browser.open(this.getRecordReportUrl(result, reportId), "_blank");
    }

    getActivityState(activity) {
        return ACTIVITY_STATES[activity.state] || ACTIVITY_STATES.planned;
    }

    formatHistoryDate(value) {
        if (!value) {
            return "";
        }
        const date = new Date(`${value.replace(" ", "T")}Z`);
        return Number.isNaN(date.getTime()) ? value : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
    }

    openRecord(record) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: record.model,
            res_id: record.id,
            views: [[false, "form"]],
            target: "current",
        });
        this.props.onClose?.();
    }

    isRecordCard(message) {
        return message.result?.type === "record";
    }

    askSuggestion(suggestion) {
        if (this.state.isAsking) {
            return;
        }
        this.state.question = suggestion;
        this.ask();
    }

    askExample(example) {
        this.state.question = example.question;
        this.ask();
    }

    /**
     * Whether the conversation is new: the greeting and the composer are centered,
     * with the use cases under them.
     */
    get isEmptyChat() {
        return !this.state.isLoading && !this.state.messages.length;
    }

    get greeting() {
        const hour = new Date().getHours();
        const firstName = (this.userName || "").split(" ")[0];
        if (hour < 5 || hour >= 18) {
            return _t("Good evening, %s", firstName);
        }
        return hour < 12 ? _t("Good morning, %s", firstName) : _t("Good afternoon, %s", firstName);
    }

    get capabilityHintText() {
        const capability = AI_CHAT_CAPABILITIES.find((c) => c.key === this.state.capabilityHint);
        return capability ? capability.description : _t("What I can do: pick one to try it");
    }

    /**
     * The things the assistant can do, as the settings allow them.
     */
    get capabilities() {
        return AI_CHAT_CAPABILITIES.filter((capability) => capability.key !== "deep" || this.state.deepAvailable)
            .map((capability) => {
                const example = this.state.examples[capability.key];
                return typeof example === "string" ? { ...capability, text: example } : capability;
            });
    }

    useCapability(capability) {
        if (capability.action === "ask") {
            this.askExample({ question: capability.text });
        } else if (capability.action === "attach") {
            this.openFilePicker();
        } else if (capability.action === "deep") {
            if (!this.state.isDeep) {
                this.toggleDeep();
            }
        } else {
            // the request to complete: the cursor at its end, with the records or commands it offers
            this.state.question = capability.text;
            browser.setTimeout(() => {
                const input = this.inputRef();
                if (input) {
                    input.value = this.state.question;
                    input.focus();
                    input.setSelectionRange(input.value.length, input.value.length);
                    this.updateMention(input);
                    this.updateCommand(input);
                }
            }, 0);
        }
    }

    async ask() {
        const question = this.state.question.trim();
        if (!question || this.state.isAsking) {
            return;
        }
        if (this.state.uploadingFiles.length) {
            return;
        }
        const attachments = [...this.state.attachments];
        // the records still mentioned in the text sent
        const mentions = this.state.mentions.filter((m) => question.includes(`@${m.name}`));
        // files are read, not analyzed: no deep analysis with them
        const deep = this.isDeepOn && !attachments.length;
        this.state.isAsking = true;
        this.state.question = "";
        this.state.attachments = [];
        this.state.mentions = [];
        this.closeMention();
        this.closeCommand();
        const pending = { id: `pending_${Date.now()}`, role: "user", content: question, result: false, attachments, mentions };
        this.state.messages.push(pending);
        this.shouldScroll = true;
        if (deep) {
            this.startDeepSteps();
        }
        try {
            const answer = await this.orm.call(CONVERSATION_MODEL, "ask_question", [
                this.state.conversationId,
                question,
                deep,
                attachments.map((attachment) => attachment.id),
                mentions.map((m) => ({ model: m.model, id: m.id })),
            ]);
            const conversation = answer.conversation;
            this.state.messages = [...this.state.messages.filter((m) => m.id !== pending.id), ...answer.messages];
            this.state.conversationId = conversation.id;
            this.state.conversationName = conversation.name;
            this.state.usage = answer.usage;
            this.state.conversations = [
                conversation,
                ...this.state.conversations.filter((c) => c.id !== conversation.id),
            ];
            browser.localStorage.setItem(LAST_CONVERSATION_KEY, conversation.id);
        } catch (error) {
            this.showError(error);
        } finally {
            this.stopDeepSteps();
            this.state.isAsking = false;
            this.shouldScroll = true;
            this.focusInput = true;
        }
    }

    // Files sent with a question ---------------------------------------------------

    openFilePicker() {
        this.fileInputRef()?.click();
    }

    onFileInputChange(ev) {
        this.uploadFiles([...ev.target.files]);
        ev.target.value = "";
    }

    onDragOver(ev) {
        if (ev.dataTransfer?.types?.includes("Files")) {
            ev.preventDefault();
            this.state.isDragging = true;
        }
    }

    onDragLeave() {
        this.state.isDragging = false;
    }

    onDrop(ev) {
        if (!ev.dataTransfer?.files?.length) {
            return;
        }
        ev.preventDefault();
        this.state.isDragging = false;
        this.uploadFiles([...ev.dataTransfer.files]);
    }

    async uploadFiles(files) {
        for (const file of files) {
            const extension = file.name.split(".").pop().toLowerCase();
            if (!ATTACHMENT_EXTENSIONS.includes(extension)) {
                this.notification.add(
                    _t("Only spreadsheets (CSV, XLSX, XLS, ODS), PDFs and pictures (PNG, JPG, WEBP) can be sent."),
                    { type: "warning" }
                );
                continue;
            }
            if (file.size > MAX_ATTACHMENT_SIZE) {
                this.notification.add(_t("\"%s\" is too large: send files of 10 MB at most.", file.name), { type: "warning" });
                continue;
            }
            if (this.state.attachments.length + this.state.uploadingFiles.length >= MAX_ATTACHMENTS) {
                this.notification.add(_t("Send %s files at most with a question.", MAX_ATTACHMENTS), { type: "warning" });
                break;
            }
            const uploading = { key: `${file.name}_${Date.now()}`, name: file.name };
            this.state.uploadingFiles.push(uploading);
            try {
                const dataUrl = await blobToDataUrl(file);
                const attachment = await this.orm.call(CONVERSATION_MODEL, "upload_chat_attachment", [
                    file.name,
                    dataUrl.split(",")[1] || "",
                ]);
                this.state.attachments.push(attachment);
            } catch (error) {
                this.showError(error);
            } finally {
                this.state.uploadingFiles = this.state.uploadingFiles.filter((f) => f.key !== uploading.key);
            }
        }
        this.focusInput = true;
        this.inputRef()?.focus();
    }

    removeAttachment(attachment) {
        this.state.attachments = this.state.attachments.filter((a) => a.id !== attachment.id);
    }

    formatFileSize(size) {
        if (size >= 1024 * 1024) {
            return `${(size / (1024 * 1024)).toFixed(1)} MB`;
        }
        return `${Math.max(1, Math.round((size || 0) / 1024))} KB`;
    }

    getFileIcon(file) {
        const extension = (file.name || "").split(".").pop().toLowerCase();
        if (extension === "pdf") {
            return "picture_as_pdf";
        }
        return DOCUMENT_EXTENSIONS.includes(extension) ? "image" : "table_chart";
    }

    getAttachmentUrl(attachment) {
        return `/web/content/${attachment.id}?download=true`;
    }

    isImport(message) {
        return message.result?.type === "import";
    }

    async openImportedRecords(message) {
        const action = await this.orm.call(CONVERSATION_MODEL, "get_import_records_action", [message.id]);
        await this.actionService.doAction(action);
        this.props.onClose?.();
    }

    // Deep analysis ------------------------------------------------------------

    get isDeepOn() {
        return this.state.deepAvailable && this.state.isDeep;
    }

    toggleDeep() {
        this.state.isDeep = !this.state.isDeep;
        browser.localStorage.setItem(DEEP_ANALYSIS_KEY, this.state.isDeep ? "1" : "0");
        this.focusInput = true;
        this.inputRef()?.focus();
    }

    startDeepSteps() {
        this.state.isAskingDeep = true;
        this.state.deepStep = 0;
        browser.clearInterval(this.deepInterval);
        this.deepInterval = browser.setInterval(() => {
            this.state.deepStep = Math.min(this.state.deepStep + 1, DEEP_STEPS.length - 1);
        }, DEEP_STEP_MS);
    }

    stopDeepSteps() {
        browser.clearInterval(this.deepInterval);
        this.state.isAskingDeep = false;
    }

    get deepSteps() {
        return DEEP_STEPS;
    }

    get deepToggleTitle() {
        return this.state.isDeep
            ? _t("Deep analysis is on: answers come as decisions, from several sets of data")
            : _t("Turn on deep analysis: get a decision with findings, recommendations and risks");
    }

    isAnalysis(message) {
        return message.result?.type === "analysis";
    }

    // Next steps planned as activities ----------------------------------------------

    /**
     * The activity a next step of an analysis is planned as, if any.
     */
    getStepActivity(message, index) {
        return message.result?.next_step_activities?.[String(index)] || false;
    }

    getStepActivityLabel(activity) {
        if (activity.state === "done") {
            return _t("Done");
        }
        const due = formatDate(deserializeDate(activity.date_deadline));
        return activity.state === "overdue" ? _t("Overdue since %s", due) : _t("Due %s", due);
    }

    async planNextStep(message, index) {
        if (typeof message.id !== "number" || this.getStepActivity(message, index)) {
            return;
        }
        let defaults;
        try {
            defaults = await this.orm.call(CONVERSATION_MODEL, "get_next_step_activity_defaults", [message.id, index]);
        } catch (error) {
            this.showError(error);
            return;
        }
        this.dialogService.add(NextStepActivityDialog, {
            step: message.result.next_steps[index],
            defaults,
            onConfirm: async (values) => {
                const updated = await this.orm.call(CONVERSATION_MODEL, "create_next_step_activity", [
                    message.id,
                    index,
                    values,
                ]);
                const position = this.state.messages.findIndex((m) => m.id === message.id);
                if (position >= 0) {
                    this.state.messages[position] = updated;
                }
                this.notification.add(_t("The activity is planned. You find it in your activities."), {
                    type: "success",
                });
            },
        });
    }

    getConfidenceLabel(confidence) {
        return {
            high: _t("High confidence"),
            medium: _t("Medium confidence"),
            low: _t("Low confidence"),
        }[confidence] || "";
    }

    /**
     * Show an error in the conversation. Errors that are not raised by the server
     * are bugs: they are raised again.
     */
    showError(error) {
        const message = error instanceof RPCError ? error.data?.message || error.message : String(error);
        this.addErrorMessage(message);
        if (!(error instanceof RPCError)) {
            throw error;
        }
    }

    addErrorMessage(message) {
        this.state.messages.push({
            id: `error_${Date.now()}`,
            role: "assistant",
            content: message,
            is_error: true,
            result: false,
        });
        this.shouldScroll = true;
    }

    // Voice questions ----------------------------------------------------------

    get showsMicrophone() {
        return this.state.voice && this.canRecord;
    }

    async startRecording() {
        if (this.recorder || this.state.isAsking || this.state.isTranscribing) {
            return;
        }
        const recorder = new VoiceRecorder({ onSeconds: (seconds) => (this.state.recordingSeconds = seconds) });
        try {
            await recorder.start();
        } catch {
            this.addErrorMessage(_t("The microphone cannot be used. Please allow this page to access it."));
            return;
        }
        this.recorder = recorder;
        this.state.recordingSeconds = 0;
        this.state.isRecording = true;
        const blob = await recorder.result;
        this.recorder = null;
        this.state.isRecording = false;
        this.focusInput = true;
        if (blob) {
            await this.askRecording(blob);
        }
    }

    /**
     * Stop the recording, and ask the question said once it is turned into text.
     */
    stopRecording() {
        this.recorder?.stop();
    }

    cancelRecording() {
        this.recorder?.cancel();
    }

    async askRecording(blob) {
        this.state.isTranscribing = true;
        let question;
        try {
            let audio;
            try {
                audio = await toVoiceAudio(blob);
            } catch {
                this.addErrorMessage(_t("The recording could not be read. Please try again."));
                return;
            }
            const transcription = await this.orm.call(CONVERSATION_MODEL, "transcribe_audio", [audio]);
            this.state.usage = transcription.usage;
            question = transcription.text;
        } catch (error) {
            this.showError(error);
            return;
        } finally {
            this.state.isTranscribing = false;
        }
        if (!question) {
            this.addErrorMessage(_t("No question was heard. Please speak closer to the microphone."));
            return;
        }
        this.state.question = question;
        await this.ask();
    }

    get inputPlaceholder() {
        if (this.state.isTranscribing) {
            return _t("Turning your voice into text...");
        }
        if (this.state.attachments.length) {
            return _t("Say what to do with the file, e.g. create customers from it, or a vendor bill from this PDF");
        }
        return this.isDeepOn
            ? _t("Ask for a decision, e.g. how can I increase the sales of a product?")
            : _t("Ask about your sales, purchases, invoices... @ mentions a record, / runs a command");
    }

    get recordingTime() {
        const seconds = this.state.recordingSeconds;
        return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
    }

    // Usage --------------------------------------------------------------------

    async refreshBalance() {
        this.state.isRefreshingBalance = true;
        try {
            this.state.usage = await this.orm.call(CONVERSATION_MODEL, "get_usage", [true]);
        } finally {
            this.state.isRefreshingBalance = false;
        }
    }

    formatTokens(tokens) {
        tokens = tokens || 0;
        if (tokens >= 1e6) {
            return `${(tokens / 1e6).toFixed(1)}M`;
        }
        if (tokens >= 1e4) {
            return `${(tokens / 1e3).toFixed(1)}k`;
        }
        return tokens.toLocaleString();
    }

    formatCost(cost) {
        if (!cost) {
            return "$0";
        }
        // AI costs are fractions of cents: keep the significant digits
        return cost >= 1 ? `$${cost.toFixed(2)}` : `$${Number(cost.toPrecision(3))}`;
    }

    formatBalance(amount) {
        return `$${(amount || 0).toFixed(2)}`;
    }

    formatDuration(seconds) {
        seconds = Math.round(seconds || 0);
        if (seconds < 60) {
            return _t("%s s", seconds);
        }
        const minutes = Math.floor(seconds / 60);
        return _t("%(minutes)s min %(seconds)s s", { minutes, seconds: String(seconds % 60).padStart(2, "0") });
    }

    /**
     * Whether to show the usage of voice questions: when they are enabled, or were.
     */
    get showsVoiceUsage() {
        const voice = this.state.usage?.voice;
        return Boolean(voice) && (this.state.voice || voice.user.recordings > 0 || voice.company?.recordings > 0);
    }

    get usageTooltip() {
        const { tokens, cost } = this.state.usage.user;
        return _t("You spent %(cost)s (%(tokens)s tokens)", {
            cost: this.formatCost(cost),
            tokens: this.formatTokens(tokens),
        });
    }

    get headerTitle() {
        return this.state.conversationName || (this.props.compact ? _t("AI Assistant") : _t("New chat"));
    }

    get balanceLabel() {
        const kind = this.state.usage?.balance?.kind;
        return kind === "key" ? _t("Key limit left") : _t("Balance");
    }

    // Results ------------------------------------------------------------------

    /**
     * The AI that made an answer, shown after it: the decision model (Jev) that chose
     * the data, then the AI that wrote a part of it (Odoo AI, or a model of OpenRouter).
     */
    getEngines(message) {
        const source = message.source;
        const engines = [];
        if (source === "deep") {
            engines.push({ kind: "deep", icon: "lightbulb", label: _t("Deep analysis"), title: _t("Deep analysis") });
        }
        if (message.decision_model) {
            engines.push({
                kind: "decision",
                icon: "account_tree",
                label: /jev/i.test(message.decision_model) ? "Jev" : message.decision_model,
                title: _t("Data chosen by the decision model %s", message.decision_model),
            });
        } else if (DECISION_SOURCES.includes(source)) {
            engines.push({ kind: "decision", icon: "account_tree", label: _t("AI decision"), title: _t("Data chosen by the decision model") });
        } else if (CACHE_SOURCES.includes(source)) {
            engines.push({ kind: "cache", icon: "flash_on", label: _t("From cache"), title: _t("Decisions reused from the cache: the decision model was not called") });
        }
        if (message.text_model) {
            engines.push({
                kind: "openrouter",
                icon: "cloud",
                label: message.text_model,
                title: _t("Written by the OpenRouter model %s", message.text_model),
            });
        } else if (message.used_olg || OLG_SOURCES.includes(source)) {
            engines.push({ kind: "olg", icon: "wand_stars", label: _t("Odoo AI"), title: _t("Written by Odoo's AI service") });
        }
        if (!engines.length || (engines.length === 1 && engines[0].kind === "deep")) {
            engines.push({ kind: "none", icon: "block", label: SOURCE_LABELS.local, title: SOURCE_LABELS.local });
        }
        return engines;
    }

    getSourceLabel(message) {
        return this.getEngines(message).map((engine) => engine.label).join(" + ");
    }

    /**
     * Whether the text of an answer says more than its result card: errors, analyses
     * and plain replies do, while the summary of a query repeats the card.
     */
    showsText(message) {
        if (this.isAnalysis(message)) {
            // the decision card shows the whole answer
            return false;
        }
        if (this.isImport(message)) {
            return true;
        }
        if (this.isRecordCard(message) || this.isExplanation(message) || this.isPrint(message)) {
            // the card shows the record
            return false;
        }
        if (message.role !== "assistant" || !message.result || message.is_error || this.isDraft(message) || this.isPlan(message)) {
            return true;
        }
        return ["openrouter_olg", "cache_olg"].includes(message.source);
    }

    getResultSummary(result) {
        const shown = result.rows?.length || 0;
        if (result.type !== "table") {
            return "";
        }
        if (!shown) {
            return _t("No matching record");
        }
        if (result.total > shown) {
            return _t("%(shown)s of %(total)s", { shown, total: result.total });
        }
        return result.total === 1 ? _t("1 result") : _t("%s results", result.total);
    }

    /**
     * The figures of a key-figure answer: a count, or the aggregates of the records.
     */
    getValueItems(result) {
        if (result.rows?.length && result.columns?.length) {
            return result.columns.map((column, index) => ({
                label: column.label,
                value: result.rows[0].cells[index],
            }));
        }
        return [{ label: result.label, value: result.value }];
    }

    // Records to create ---------------------------------------------------------

    isDraft(message) {
        return message.result?.type === "draft";
    }

    /**
     * Whether an answer is a plan: records to create one after the other, as the
     * first ones are needed by the next ones (a new customer for a new order).
     */
    isPlan(message) {
        return message.result?.type === "plan";
    }

    isCurrentStep(plan, index) {
        return plan.state === "draft" && plan.current === index;
    }

    getPlanProgress(plan) {
        if (plan.state === "discarded") {
            return _t("Discarded");
        }
        const created = plan.steps.filter((step) => step.state === "created").length;
        return _t("%(created)s of %(count)s created", { created, count: plan.steps.length });
    }

    getDraftSummary(draft) {
        return draft.fields.map((field) => field.value).join(" · ");
    }

    canCreateDraft(draft) {
        const { state, missing, fields, lines } = draft;
        return state === "draft" && !missing?.length && Boolean(fields?.length || lines?.length);
    }

    /**
     * Run an action on a draft answer, and show the answer the server returns.
     */
    async updateDraft(message, method) {
        if (this.state.pendingDraftId) {
            return;
        }
        this.state.pendingDraftId = message.id;
        try {
            const updated = await this.orm.call(CONVERSATION_MODEL, method, [message.id]);
            const index = this.state.messages.findIndex((m) => m.id === message.id);
            this.state.messages[index] = updated;
        } catch (error) {
            this.showError(error);
        } finally {
            this.state.pendingDraftId = false;
        }
    }

    createDraft(message) {
        return this.updateDraft(message, "create_draft_record");
    }

    discardDraft(message) {
        return this.updateDraft(message, "discard_draft");
    }

    async editDraft(message) {
        const action = await this.orm.call(CONVERSATION_MODEL, "get_draft_form_action", [message.id]);
        await this.actionService.doAction(action);
        this.props.onClose?.();
    }

    openCreatedRecord(draft) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: draft.model,
            res_id: draft.res_id,
            views: [[false, "form"]],
            target: "current",
        });
        this.props.onClose?.();
    }

    // Downloads -----------------------------------------------------------------

    /**
     * Whether an answer can be downloaded: answers saved on the server, with data.
     */
    canDownload(message) {
        return (
            Number.isInteger(message.id) &&
            Boolean(message.result) &&
            !this.isDraft(message) &&
            !this.isPlan(message) &&
            !this.isImport(message) &&
            !this.isRecordCard(message) &&
            !this.isExplanation(message) &&
            !this.isPrint(message)
        );
    }

    async downloadXlsx(message) {
        await download({ url: "/ai_chat_pro/export/xlsx", data: { message_id: message.id } });
    }

    /**
     * Whether an answer makes a PDF report: answers with records or key figures.
     */
    canPrintReport(message) {
        const { type, rows } = message.result || {};
        return (
            this.canDownload(message) &&
            !message.is_error &&
            REPORT_RESULT_TYPES.includes(type) &&
            (type !== "table" || Boolean(rows?.length))
        );
    }

    /**
     * Download an answer as a PDF report, printed by the report engine of Odoo. The
     * chart shown is printed in it: the report engine does not draw charts.
     */
    async downloadReport(message) {
        if (this.state.printingReportId) {
            return;
        }
        // without a PDF engine on the server, the report opens to be printed by the browser: the
        // tab is opened now, while the click allows it, as popups are blocked after a wait
        const printTab = !this.state.pdfEngine && browser.open("", `ai_chat_report_${message.id}`);
        this.state.printingReportId = message.id;
        try {
            const data = { message_id: message.id };
            if (this.getResultView(message) === "chart") {
                const blob = await this.chartExports[message.id]?.();
                if (blob) {
                    data.chart = await blobToDataUrl(blob);
                }
            }
            if (this.state.pdfEngine) {
                await download({ url: "/ai_chat_pro/report/pdf", data });
            } else if (printTab) {
                postInTab("/ai_chat_pro/report/html", data, printTab.name);
            } else {
                this.addErrorMessage(_t("Allow pop-ups for this site to open the report."));
            }
        } finally {
            this.state.printingReportId = false;
        }
    }

    get reportButtonLabel() {
        return this.state.pdfEngine
            ? _t("Download a PDF report")
            : _t("Open the report to print it or save it as PDF");
    }

    registerChartExport(message, exportImage) {
        this.chartExports[message.id] = exportImage;
    }

    async downloadChart(message) {
        const blob = await this.chartExports[message.id]?.();
        if (blob) {
            const name = (message.result.heading || "chart").replace(/[^\p{L}\p{N}-]+/gu, "_").slice(0, 60);
            downloadFile(blob, `${name}.png`, "image/png");
        }
    }

    getResultView(message) {
        const chart = message.result?.chart;
        if (!chart) {
            return "table";
        }
        return this.state.resultViews[message.id] || (chart.preferred ? "chart" : "table");
    }

    setResultView(message, view) {
        this.state.resultViews[message.id] = view;
    }

    getChartType(message) {
        return this.state.chartTypes[message.id] || message.result.chart.type;
    }

    setChartType(message, type) {
        this.state.chartTypes[message.id] = type;
        this.state.resultViews[message.id] = "chart";
    }

    onRowKeydown(ev, result, row) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            this.openRecord(result, row);
        }
    }

    openRecord(result, row) {
        if (!result.openable || !row.id) {
            return;
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            // the rows of a grouped answer are the records it is grouped by
            res_model: result.row_model || result.model,
            res_id: row.id,
            views: [[false, "form"]],
            target: "current",
        });
        this.props.onClose?.();
    }

    openList(result) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: result.title,
            res_model: result.model,
            domain: result.domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: "current",
        });
        this.props.onClose?.();
    }
}
