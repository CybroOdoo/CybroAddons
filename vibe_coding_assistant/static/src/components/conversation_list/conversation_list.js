import { Component, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

// ── Module-level helper: format datetime as relative "x ago" ─────────────

function relativeTime(dt) {
    if (!dt) return "";
    // Odoo returns datetimes as "YYYY-MM-DD HH:MM:SS" strings (local server time).
    const parsed = typeof dt === "string"
        ? new Date(dt.replace(" ", "T"))
        : dt;
    if (isNaN(parsed.getTime())) return "";

    const seconds = Math.floor((Date.now() - parsed.getTime()) / 1000);
    if (seconds < 60)    return _t("just now");
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60)    return _t("%sm ago", minutes);
    const hours = Math.floor(minutes / 60);
    if (hours < 24)      return _t("%sh ago", hours);
    const days = Math.floor(hours / 24);
    if (days < 7)        return _t("%sd ago", days);
    const weeks = Math.floor(days / 7);
    if (weeks < 5)       return _t("%sw ago", weeks);
    const months = Math.floor(days / 30);
    if (months < 12)     return _t("%smo ago", months);
    return _t("%sy ago", Math.floor(days / 365));
}

// ── Component ─────────────────────────────────────────────────────────────

export class ConversationList extends Component {
    static template = "vibe_coding_assistant.ConversationList";

    setup() {
        this.vibeStore = proxy(useService("vibeStore"));
        this.state = proxy({ filter: "" });
    }

    /** Conversations filtered by the search box (case-insensitive). */
    get conversations() {
        const all = this.vibeStore.state.conversations || [];
        const q = this.state.filter.trim().toLowerCase();
        if (!q) return all;
        return all.filter((c) => (c.name || "").toLowerCase().includes(q));
    }

    get isLoading() {
        return this.vibeStore.state.isLoadingConversations;
    }

    get isEmpty() {
        return (this.vibeStore.state.conversations || []).length === 0;
    }

    get noResults() {
        return !this.isEmpty && this.conversations.length === 0;
    }

    isActive(id) {
        return this.vibeStore.state.activeConversationId === id;
    }

    timeLabel(conv) {
        return relativeTime(conv.last_activity);
    }

    /** First letter for the avatar circle — falls back to "·" for empty names. */
    initial(conv) {
        const s = (conv.name || "").trim();
        if (!s) return "·";
        // Skip leading emoji/symbols, grab first letter or digit
        const m = s.match(/[\p{L}\p{N}]/u);
        return m ? m[0].toUpperCase() : s[0];
    }

    onClearFilter() {
        this.state.filter = "";
    }

    /** URL for downloading the conversation as JSON.
     *  Returned as a string so the anchor's native download behaviour works
     *  (browser shows a download prompt, no JS fetch needed).
     */
    exportUrl(id) {
        return "/vibe/conversation/" + id + "/export";
    }

    async onNewChat() {
        await this.vibeStore.newConversation();
    }

    async onSelect(id) {
        await this.vibeStore.selectConversation(id);
    }

    async onArchive(id) {
        await this.vibeStore.archiveConversation(id);
    }
}
