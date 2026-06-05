/** @odoo-module **/

import { Component, useState, useEffect, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class Composer extends Component {
    static template = "vibe_coding_assistant.Composer";

    setup() {
        this.vibeStore = useService("vibeStore");
        this.storeState = useState(this.vibeStore.state);
        this.state = useState({ text: "" });
        this.textareaRef = useRef("textarea");

        // React to template-chip clicks: when storeState.pendingPromptInsert
        // becomes non-null, drop the prompt text into the textarea, focus it,
        // and clear the signal so the same click doesn't fire twice.
        useEffect(
            (pending) => {
                if (pending) {
                    this.state.text = pending;
                    this.vibeStore.state.pendingPromptInsert = null;
                    // Defer focus to next tick so the DOM has updated
                    Promise.resolve().then(() => {
                        const el = this.textareaRef.el;
                        if (el) {
                            el.focus();
                            // Move caret to end so the user can keep typing
                            el.setSelectionRange(el.value.length, el.value.length);
                        }
                    });
                }
            },
            () => [this.storeState.pendingPromptInsert]
        );
    }

    get canSend() {
        return !!this.state.text.trim() && !this.storeState.isSending;
    }

    /** Refine button is available when there's a previous module to refine,
     *  the text isn't empty, and we're not already sending. */
    get canRefine() {
        const conv = this.storeState.conversationTotals;
        return this.canSend && !!conv && conv.can_refine;
    }

    /** Whether to show the Refine button at all. The conversation must have
     *  produced at least one module — otherwise the button is irrelevant. */
    get showRefine() {
        const conv = this.storeState.conversationTotals;
        return !!conv && conv.can_refine;
    }

    /** Latest module name, for the refine-button tooltip. */
    get latestModuleName() {
        const conv = this.storeState.conversationTotals;
        return conv && conv.latest_module_name || "";
    }

    get latestRevision() {
        const conv = this.storeState.conversationTotals;
        return conv && conv.latest_module_revision || 0;
    }

    get isSending() {
        return this.storeState.isSending;
    }

    /** Provider badge data — shown below the textarea. */
    get providerInfo() {
        return this.storeState.providerInfo || null;
    }

    async onSend() {
        if (!this.canSend) return;
        const text = this.state.text.trim();
        this.state.text = "";
        await this.vibeStore.sendMessage(text);
    }

    async onRefine() {
        if (!this.canRefine) return;
        const text = this.state.text.trim();
        this.state.text = "";
        await this.vibeStore.refineMessage(text);
    }

    onKeydown(ev) {
        // Ctrl+Enter: refine if available, else send
        if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") {
            ev.preventDefault();
            // Plain Ctrl+Enter still sends a fresh message even when Refine
            // is available — fresh generation is the safer default. To
            // trigger Refine, the user clicks the Refine button explicitly.
            this.onSend();
        }
    }
}
