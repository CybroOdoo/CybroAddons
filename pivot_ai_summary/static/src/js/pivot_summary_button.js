/** @odoo-module **/
import { PivotController } from "@web/views/pivot/pivot_controller";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, onWillStart, useChildSubEnv } from "@odoo/owl";

patch(PivotController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.aiState = useState({
            isEnabled: false,
            showPanel: false,
            loading: false,
            messages: [],
            userInput: ""
        });

        useChildSubEnv({
            aiState: this.aiState,
            onAISummaryClick: () => this.onAISummaryClick(),
        });

        onWillStart(async () => {
            const enabled = await this.orm.call("pivot.ai.summary", "is_ai_enabled", []);
            this.aiState.isEnabled = !!enabled;
        });
    },

    async onAISummaryClick() {
        this.aiState.showPanel = true;
        if (this.aiState.messages.length > 0) return;

        this.aiState.loading = true;
        const tableText = this._get_table_text();

        try {
            const summary = await this.orm.call("pivot.ai.summary", "generate_summary", [tableText, []]);
            this.aiState.messages.push({ role: 'ai', content: summary });
        } catch (e) {
            this.notification.add("Analysis failed.", { type: "danger" });
        } finally {
            this.aiState.loading = false;
        }
    },

    onKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.sendMessage();
        }
    },

    async sendMessage() {
        const prompt = this.aiState.userInput.trim();
        if (!prompt || this.aiState.loading) return;

        this.aiState.messages.push({ role: 'user', content: prompt });
        const historyForBackend = JSON.parse(JSON.stringify(this.aiState.messages));

        this.aiState.userInput = "";
        this.aiState.loading = true;

        const tableText = this._get_table_text();

        try {
            const response = await this.orm.call("pivot.ai.summary", "generate_summary", [tableText, historyForBackend]);
            this.aiState.messages.push({ role: 'ai', content: response });
        } catch (error) {
            this.notification.add("Chat error occurred.", { type: "danger" });
        } finally {
            this.aiState.loading = false;
        }
    },

    _get_table_text() {
        const tableEl = document.querySelector(".o_pivot_table") || document.querySelector(".o_content table");
        if (!tableEl) return "";
        const lines = [];
        tableEl.querySelectorAll("tr").forEach((tr) => {
            const cells = Array.from(tr.querySelectorAll("th, td")).map(c => c.innerText.trim()).filter(c => c !== "");
            if (cells.length > 0) lines.push(cells.join(" | "));
        });
        return lines.join("\n");
    }
});

patch(PivotRenderer.prototype, {
    setup() {
        super.setup();
        this.aiState = this.env.aiState;
    },
    onAISummaryClick() {
        this.env.onAISummaryClick();
    }
});
