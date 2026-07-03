/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ── Provider icon/color mapping ───────────────────────────────────────────────
const PROVIDER_ICONS = {
    openai:    "fa-circle-o",
    anthropic: "fa-cube",
    google:    "fa-diamond",
    ollama:    "fa-home",
    custom:    "fa-plug",
};
const PROVIDER_COLORS = {
    openai:    "#10A37F",
    anthropic: "#C68642",
    google:    "#4285F4",
    ollama:    "#7C3AED",
    custom:    "#6B7280",
};

// ── Main Dashboard Component ──────────────────────────────────────────────────
export class McpDashboard extends Component {
    static template = "odoo_mcp_manager.McpDashboard";
    static props = ["*"];

    setup() {
        this.orm           = useService("orm");
        this.actionService = useService("action");

        this.state = useState({
            loading:     true,
            data:        null,
            lastRefresh: null,
            spinning:    false,
        });

        this._pollInterval = null;

        onMounted(() => {
            this._fetchData();
            this._pollInterval = setInterval(() => this._fetchData(), 15000);
        });

        onWillUnmount(() => {
            if (this._pollInterval) clearInterval(this._pollInterval);
        });
    }

    // ── Data fetching ─────────────────────────────────────────────────────
    async _fetchData() {
        try {
            const data = await this.orm.call("ai.dashboard", "get_dashboard_data", []);
            this.state.data        = data;
            this.state.loading     = false;
            this.state.lastRefresh = new Date().toLocaleTimeString();
        } catch (e) {
            console.error("McpDashboard: fetch failed", e);
            this.state.loading = false;
        }
    }

    async onRefresh() {
        this.state.spinning = true;
        await this._fetchData();
        setTimeout(() => { this.state.spinning = false; }, 600);
    }

    // ── Navigation ────────────────────────────────────────────────────────
    _doAction(xmlId) {
        this.actionService.doAction(xmlId);
    }

    async openSessions()  { this._doAction("odoo_mcp_manager.ai_session_action"); }
    async openLogs()      { this._doAction("odoo_mcp_manager.ai_tool_log_action"); }
    async openConsents()  { this._doAction("odoo_mcp_manager.ai_consent_action"); }
    async openProviders() { this._doAction("odoo_mcp_manager.ai_provider_action"); }
    async openTools()     { this._doAction("odoo_mcp_manager.ai_tool_action"); }
    async openKeys()      { this._doAction("odoo_mcp_manager.ai_generate_mcp_key_action"); }

    // ── Template helpers ──────────────────────────────────────────────────
    get statusBadgeClass() {
        return this.state.data?.status === "active" ? "badge-active" : "badge-inactive";
    }
    get statusLabel() {
        return (this.state.data?.status || "active").toUpperCase();
    }

    providerIcon(service)    { return PROVIDER_ICONS[service]  || "fa-plug"; }
    providerColor(service)   { return PROVIDER_COLORS[service] || "#6B7280"; }

    activityStatusClass(status) {
        return { success: "status-success", error: "status-error", pending: "status-pending" }[status] || "status-success";
    }
    activityStatusLabel(status) {
        return { success: "Success", error: "Error", pending: "Pending Approval" }[status] || "Success";
    }

    deltaClass(delta, higherIsBetter = true) {
        if (!delta) return "";
        const pos = delta.startsWith("+");
        return higherIsBetter ? (pos ? "delta-good" : "delta-bad") : (pos ? "delta-bad" : "delta-good");
    }
}

// ── Register as client action ─────────────────────────────────────────────────
registry.category("actions").add("mcp_gateway_dashboard", McpDashboard);
