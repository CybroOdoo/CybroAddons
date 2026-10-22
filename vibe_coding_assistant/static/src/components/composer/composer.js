import { Component, proxy, signal, useEffect, onPatched } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class Composer extends Component {
    static template = "vibe_coding_assistant.Composer";

    // OWL 3: refs are signal.ref() class fields, accessed as this.ref() not this.ref.el
    textareaRef = signal.ref();

    setup() {
        // proxy(useService(...)) is the OWL 3 pattern for reactive shared state
        this.vibeStore = proxy(useService("vibeStore"));
        this.state = proxy({ text: "" });

        // React to template-chip clicks: when pendingPromptInsert becomes non-null,
        // insert the text into the textarea, focus it, and clear the signal.
        // OWL 20 useEffect: single callback, deps tracked automatically by reading
        // reactive state inside the callback. No deps-getter second argument.
        useEffect(() => {
            const pending = this.vibeStore.state.pendingPromptInsert;
            if (pending) {
                this.state.text = pending;
                this.vibeStore.state.pendingPromptInsert = null;
            }
        });

        // After every OWL patch, if state.text was just set by a chip click,
        // sync the DOM textarea .value property directly and focus it.
        // t-att-value only sets the HTML attribute; once the user has interacted
        // with the textarea the browser decouples the attribute from .value, so
        // we must set the property directly.
        onPatched(() => {
            const el = this.textareaRef();
            if (el && el.value !== this.state.text) {
                el.value = this.state.text;
                el.dispatchEvent(new Event("input", { bubbles: true }));
                el.focus();
                el.setSelectionRange(el.value.length, el.value.length);
            }
        });
    }

    get canSend() {
        return !!this.state.text.trim() && !this.vibeStore.state.isSending;
    }

    /** Refine button is available when there's a previous module to refine,
     *  the text isn't empty, and we're not already sending. */
    get canRefine() {
        const conv = this.vibeStore.state.conversationTotals;
        return this.canSend && !!conv && conv.can_refine;
    }

    /** Whether to show the Refine button at all. The conversation must have
     *  produced at least one module — otherwise the button is irrelevant. */
    get showRefine() {
        const conv = this.vibeStore.state.conversationTotals;
        return !!conv && conv.can_refine;
    }

    /** Latest module name, for the refine-button tooltip. */
    get latestModuleName() {
        const conv = this.vibeStore.state.conversationTotals;
        return conv && conv.latest_module_name || "";
    }

    get latestRevision() {
        const conv = this.vibeStore.state.conversationTotals;
        return conv && conv.latest_module_revision || 0;
    }

    get isSending() {
        return this.vibeStore.state.isSending;
    }

    /** Provider badge data — shown below the textarea. */
    get providerInfo() {
        return this.vibeStore.state.providerInfo || null;
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
        // Ctrl+Enter → send
        if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") {
            ev.preventDefault();
            this.onSend();
        }
    }
}
