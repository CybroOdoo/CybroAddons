import { Component, proxy, signal, useEffect, onPatched } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

// ── Module-level: rough tokens-per-second by model family ─────────────────
const TOKENS_PER_SEC_BY_PREFIX = [
    [/^gemini-(2\.5|2\.0)-flash-lite/i, 90],
    [/^gemini-(2\.5|2\.0)-flash/i,      75],
    [/^gemini-(2\.5|2\.0)-pro/i,        35],
    [/^gemini-1\.5-flash/i,             80],
    [/^gemini-1\.5-pro/i,               40],
    [/^claude(-.*)?-haiku/i,            80],
    [/^claude(-.*)?-sonnet/i,           50],
    [/^claude(-.*)?-opus/i,             30],
    [/^gpt-4o-mini/i,                   60],
    [/^gpt-4o/i,                        40],
    [/^o1/i,                            25],
    [/^o3/i,                            35],
];
const DEFAULT_TOKENS_PER_SEC = 40;

function tokensPerSec(modelName) {
    for (const [re, tps] of TOKENS_PER_SEC_BY_PREFIX) {
        if (re.test(modelName || "")) return tps;
    }
    return DEFAULT_TOKENS_PER_SEC;
}

// Labels are resolved lazily in `progressLabel` so _t() runs after the
// translations are loaded (module-level _t() calls would not be translated).
const PHASE_SENDING  = { id: "sending",  icon: "send" };
const PHASE_THINKING = { id: "thinking", icon: "autorenew" };
const PHASE_SWITCH_MS = 600;

export class MessageThread extends Component {
    static template = "vibe_coding_assistant.MessageThread";

    // OWL 3: refs are signal.ref() class fields, accessed as this.ref() not this.ref.el
    threadRef = signal.ref();

    setup() {
        // proxy(useService(...)) is the OWL 3 pattern for reactive shared state
        this.vibeStore = proxy(useService("vibeStore"));

        this.progress = proxy({
            startedAt: 0,
            elapsedMs: 0,
            phase: PHASE_SENDING,
        });
        this._tickHandle = null;

        // Auto-scroll to newest message after every render
        onPatched(() => {
            const el = this.threadRef();
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        });

        // Start/stop the 200ms tick timer when isSending toggles.
        useEffect(() => {
            const sending = this.vibeStore.state.isSending;
            if (sending) {
                this.progress.startedAt = Date.now();
                this.progress.elapsedMs = 0;
                this.progress.phase = PHASE_SENDING;
                this._tickHandle = setInterval(() => {
                    const elapsed = Date.now() - this.progress.startedAt;
                    this.progress.elapsedMs = elapsed;
                    if (elapsed > PHASE_SWITCH_MS && this.progress.phase.id === "sending") {
                        this.progress.phase = PHASE_THINKING;
                    }
                }, 200);
            } else {
                if (this._tickHandle) {
                    clearInterval(this._tickHandle);
                    this._tickHandle = null;
                }
            }
            return () => {
                if (this._tickHandle) {
                    clearInterval(this._tickHandle);
                    this._tickHandle = null;
                }
            };
        });
    }

    get messages() {
        return this.vibeStore.state.messages;
    }

    get isSending() {
        return this.vibeStore.state.isSending;
    }

    get hasConversation() {
        return !!this.vibeStore.state.activeConversationId;
    }

    async onViewModule(moduleId) {
        const id = Array.isArray(moduleId) ? moduleId[0] : moduleId;
        await this.vibeStore.selectModule(id);
    }

    downloadUrl(moduleId) {
        const id = Array.isArray(moduleId) ? moduleId[0] : moduleId;
        return `/vibe/module/${id}/download`;
    }

    formatTokens(n) {
        const v = Number(n) || 0;
        if (v === 0) return "0";
        if (v < 1000) return String(v);
        if (v < 10000) return (v / 1000).toFixed(1).replace(/\.0$/, "") + "k";
        return Math.round(v / 1000) + "k";
    }

    get conversationTotals() {
        return this.vibeStore.state.conversationTotals || null;
    }

    get templatesByCategory() {
        const CATEGORY_LABELS = {
            crud:        _t("CRUD Modules"),
            inherit:     _t("Extend Existing"),
            report:      _t("Reports"),
            wizard:      _t("Wizards"),
            integration: _t("Integrations"),
            other:       _t("Other"),
        };
        const ORDER = ["crud", "inherit", "report", "wizard", "integration", "other"];

        const groups = {};
        for (const tpl of this.vibeStore.state.promptTemplates || []) {
            const cat = tpl.category || "other";
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(tpl);
        }
        const out = [];
        for (const cat of ORDER) {
            if (groups[cat] && groups[cat].length) {
                out.push({
                    category: cat,
                    label: CATEGORY_LABELS[cat] || cat,
                    items: groups[cat],
                });
            }
        }
        return out;
    }

    onChipClick(tpl) {
        this.vibeStore.state.pendingPromptInsert = tpl.prompt;
    }

    categoryIcon(category) {
        const ICONS = {
            crud:        "deployed_code",
            inherit:     "share",
            report:      "description",
            wizard:      "star",
            integration: "power",
            other:       "grid_view",
        };
        return ICONS[category] || "bookmark";
    }

    get progressLabel() {
        return this.progress.phase.id === "thinking"
            ? _t("AI is thinking…")
            : _t("Sending request to AI…");
    }

    get progressClass() {
        // Spin the icon while the AI is "thinking".
        return this.progress.phase.id === "thinking"
            ? "oi me-1 oi-spin"
            : "oi me-1";
    }

    get progressIcon() {
        return this.progress.phase.icon;
    }

    get progressElapsed() {
        const totalSec = Math.floor(this.progress.elapsedMs / 1000);
        if (totalSec < 60) return totalSec + "s";
        const m = Math.floor(totalSec / 60);
        const s = totalSec % 60;
        return s ? `${m}m ${s}s` : `${m}m`;
    }

    get progressTokenEstimate() {
        const elapsedSec = this.progress.elapsedMs / 1000;
        if (elapsedSec < 1.5) return "";
        const info = this.vibeStore.state.providerInfo;
        const modelName = (info && info.model) || "";
        const tps = tokensPerSec(modelName);
        const est = Math.floor(elapsedSec * tps);
        return est.toLocaleString();
    }
}
