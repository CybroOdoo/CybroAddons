/** @odoo-module **/

import { Component, useRef, onPatched, useState, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// ── Module-level: rough tokens-per-second by model family ─────────────────
// Used only for the "estimated tokens" counter shown while generating.
// These are deliberately low-ball estimates — better to under-promise so the
// real token count shown in the final card feels like a pleasant surprise.
// Generated text only; we don't try to estimate prompt tokens (the user's
// prompt is short and already known on the client).
const TOKENS_PER_SEC_BY_PREFIX = [
    [/^gemini-(2\.5|2\.0)-flash-lite/i, 90],
    [/^gemini-(2\.5|2\.0)-flash/i,      75],
    [/^gemini-(2\.5|2\.0)-pro/i,        35],
    [/^gemini-1\.5-flash/i,             80],
    [/^gemini-1\.5-pro/i,               40],
    // Claude — match both old (claude-3-5-sonnet) and new (claude-sonnet-4-5) styles
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

// ── Phase definitions ─────────────────────────────────────────────────────
// Mostly cosmetic: the server returns a single response so we can't actually
// observe phase transitions. The "Sending" phase is brief and deterministic;
// the "Thinking" phase is where 95% of real time is spent. Pretending there
// are stages is a UX trick — it makes the wait feel less indefinite.
const PHASE_SENDING  = { id: "sending",  label: "Sending request to AI…",  icon: "fa fa-paper-plane" };
const PHASE_THINKING = { id: "thinking", label: "AI is thinking…",          icon: "fa fa-cog fa-spin" };

// After this many ms we switch from "Sending" to "Thinking"
const PHASE_SWITCH_MS = 600;

export class MessageThread extends Component {
    static template = "vibe_coding_assistant.MessageThread";

    setup() {
        this.vibeStore = useService("vibeStore");
        this.storeState = useState(this.vibeStore.state);
        this.threadRef = useRef("thread");

        // Local UI state for the progress indicator
        this.progress = useState({
            startedAt: 0,
            elapsedMs: 0,
            phase: PHASE_SENDING,
        });
        this._tickHandle = null;

        // Auto-scroll to newest message after every render
        onPatched(() => {
            const el = this.threadRef.el;
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        });

        // Start/stop the 200ms tick timer when isSending toggles.
        useEffect(
            (sending) => {
                if (sending) {
                    this.progress.startedAt = Date.now();
                    this.progress.elapsedMs = 0;
                    this.progress.phase = PHASE_SENDING;
                    this._tickHandle = setInterval(() => {
                        const elapsed = Date.now() - this.progress.startedAt;
                        this.progress.elapsedMs = elapsed;
                        // Promote to "Thinking" once we've been waiting more than ~0.6s
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
                // Cleanup on unmount too
                return () => {
                    if (this._tickHandle) {
                        clearInterval(this._tickHandle);
                        this._tickHandle = null;
                    }
                };
            },
            () => [this.storeState.isSending]
        );
    }

    get messages() {
        return this.storeState.messages;
    }

    get isSending() {
        return this.storeState.isSending;
    }

    get hasConversation() {
        return !!this.storeState.activeConversationId;
    }

    /** Phase 4: called when user clicks "View files" on a module card */
    async onViewModule(moduleId) {
        await this.vibeStore.selectModule(moduleId);
    }

    /** Phase 4: return the download URL for a generated module */
    downloadUrl(moduleId) {
        return `/vibe/module/${moduleId}/download`;
    }

    /** Format a token count as "1.2k" / "847" for compact display. */
    formatTokens(n) {
        const v = Number(n) || 0;
        if (v === 0) return "0";
        if (v < 1000) return String(v);
        if (v < 10000) return (v / 1000).toFixed(1).replace(/\.0$/, "") + "k";
        return Math.round(v / 1000) + "k";
    }

    /** Conversation-wide totals for the header strip. */
    get conversationTotals() {
        return this.storeState.conversationTotals || null;
    }

    /** Prompt templates grouped by category for the empty-state chip strip.
     *
     * Returns an array of {category, label, items[]} groups, in a stable
     * presentation order (CRUD first, then Extend, etc.). Categories with
     * no active templates are omitted.
     */
    get templatesByCategory() {
        const CATEGORY_LABELS = {
            crud:        "CRUD Modules",
            inherit:     "Extend Existing",
            report:      "Reports",
            wizard:      "Wizards",
            integration: "Integrations",
            other:       "Other",
        };
        const ORDER = ["crud", "inherit", "report", "wizard", "integration", "other"];

        const groups = {};
        for (const tpl of this.storeState.promptTemplates || []) {
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

    /** User clicked a template chip — signal the composer to insert the text. */
    onChipClick(tpl) {
        this.vibeStore.state.pendingPromptInsert = tpl.prompt;
    }

    /** Font Awesome class for each category card. */
    categoryIcon(category) {
        const ICONS = {
            crud:        "fa fa-cube",
            inherit:     "fa fa-code-fork",
            report:      "fa fa-file-text-o",
            wizard:      "fa fa-magic",
            integration: "fa fa-plug",
            other:       "fa fa-th-large",
        };
        return ICONS[category] || "fa fa-bookmark";
    }

    // ── Progress indicator getters ────────────────────────────────────────

    get progressLabel() {
        return this.progress.phase.label;
    }

    get progressIcon() {
        return this.progress.phase.icon;
    }

    /** Elapsed time formatted as "3s" / "1m 12s". */
    get progressElapsed() {
        const totalSec = Math.floor(this.progress.elapsedMs / 1000);
        if (totalSec < 60) return totalSec + "s";
        const m = Math.floor(totalSec / 60);
        const s = totalSec % 60;
        return s ? `${m}m ${s}s` : `${m}m`;
    }

    /** Rough token estimate based on model speed × elapsed time.
     *
     * Returns a string like "1,200" or "" when we don't have enough signal yet
     * (first second, or no provider info loaded). The number is deliberately
     * low — under-promising avoids the bad case where the real count comes in
     * smaller than the estimate.
     */
    get progressTokenEstimate() {
        const elapsedSec = this.progress.elapsedMs / 1000;
        // Don't show an estimate until we've waited at least 1.5s — otherwise
        // it flashes "~0 tokens" briefly which looks bad
        if (elapsedSec < 1.5) return "";
        const info = this.storeState.providerInfo;
        const modelName = (info && info.model) || "";
        const tps = tokensPerSec(modelName);
        const est = Math.floor(elapsedSec * tps);
        // Format with thousand-separators for readability
        return est.toLocaleString();
    }
}
