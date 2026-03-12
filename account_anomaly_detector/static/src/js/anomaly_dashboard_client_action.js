/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * AnomalyDashboard – full OWL client action dashboard
 * Shows KPIs, risk breakdown, alert type bars and a live feed of recent alerts.
 */
class AnomalyDashboard extends Component {
    static template = "account_anomaly_detector.AnomalyDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.rootRef = useRef("rootRef");
        this.state = useState({
            loading: true,
            isDark: false,
            kpi: {
                total: 0,
                critical: 0,
                high: 0,
                medium: 0,
                low: 0,
                open: 0,
                investigating: 0,
                escalated: 0,
                resolved_today: 0,
            },
            byType: [],
            recentAlerts: [],
            lastUpdated: null,
        });

        onWillStart(async () => {
            await this._loadDashboardData();
        });

        onMounted(() => {
            // Only activate dark mode if Odoo's color_scheme cookie is explicitly "dark".
            // If there's no cookie, light mode is the default — no OS-level fallback.
            const colorScheme = this._getCookie("color_scheme");
            const isDark = colorScheme === "dark";
            this.state.isDark = isDark;
            this._applyDarkMode(isDark);
        });
    }

    _getCookie(name) {
        const match = document.cookie.match(new RegExp("(?:^|;\\s*)" + name + "=([^;]*)"));
        return match ? decodeURIComponent(match[1]) : null;
    }

    /**
     * Applies or removes the ad-dark class on the DASHBOARD ONLY.
     * Does NOT affect the rest of Odoo's UI.
     */
    _applyDarkMode(isDark) {
        const dashboard = this.rootRef.el;
        if (!dashboard) return;
        dashboard.classList.toggle("ad-dark", isDark);
    }

    toggleTheme() {
        const dashboard = this.rootRef.el;
        if (!dashboard) return;

        const goingDark = !this.state.isDark;

        // ── Corner Circle-Wipe Animation ──────────────────────────
        // Always expands from the TOP-RIGHT corner for both directions.
        const originX = "100% 0%";
        const newBg = goingDark ? "#09090b" : "#f4f6f9";

        const overlay = document.createElement("div");
        overlay.style.cssText = `
            position: fixed;
            inset: 0;
            background: ${newBg};
            clip-path: circle(0% at ${originX});
            z-index: 9999;
            pointer-events: none;
            will-change: clip-path;
        `;
        document.body.appendChild(overlay);

        // Force reflow so the initial clip-path is applied before transitioning
        overlay.getBoundingClientRect();

        // Begin circle expansion with a smooth cubic-bezier
        overlay.style.transition = "clip-path 0.75s cubic-bezier(0.76, 0, 0.24, 1)";
        overlay.style.clipPath = `circle(150% at ${originX})`;

        // Switch the actual theme at mid-animation (380ms)
        setTimeout(() => {
            this.state.isDark = goingDark;
            this._applyDarkMode(goingDark);
        }, 380);

        // After circle fully covers the screen, fade overlay out and remove it
        setTimeout(() => {
            overlay.style.transition = "opacity 0.25s ease";
            overlay.style.opacity = "0";
            setTimeout(() => overlay.remove(), 280);
        }, 780);
    }

    async _loadDashboardData() {
        this.state.loading = true;
        try {
            const alerts = await this.orm.searchRead(
                "account.anomaly.alert",
                [],
                [
                    "id", "title", "risk_level", "alert_type", "state",
                    "anomaly_score", "detected_date", "partner_id",
                    "move_id", "move_amount", "currency_id",
                ],
                { limit: 1000, order: "anomaly_score desc, detected_date desc" }
            );

            // KPIs
            const kpi = {
                total: alerts.length,
                critical: alerts.filter(a => a.risk_level === "critical").length,
                high: alerts.filter(a => a.risk_level === "high").length,
                medium: alerts.filter(a => a.risk_level === "medium").length,
                low: alerts.filter(a => a.risk_level === "low").length,
                open: alerts.filter(a => a.state === "open").length,
                investigating: alerts.filter(a => a.state === "investigating").length,
                escalated: alerts.filter(a => a.state === "escalated").length,
                resolved_today: alerts.filter(a => a.state === "resolved").length,
            };
            this.state.kpi = kpi;

            // Alert type distribution
            const typeMap = {};
            const typeLabels = {
                amount_outlier: "Amount Outlier",
                duplicate_vendor_bill: "Duplicate Bill",
                round_number: "Round Number",
                velocity_spike: "Velocity Spike",
                unusual_timing: "Unusual Timing",
                spending_deviation: "Spending Deviation",
                benfords_violation: "Benford's Law",
                unusual_account_combo: "Unusual Account",
                vendor_concentration: "Vendor Concentration",
                manual: "Manual Flag",
            };
            const typeIcons = {
                amount_outlier: "📊", duplicate_vendor_bill: "📋",
                round_number: "🔢", velocity_spike: "⚡",
                unusual_timing: "🕐", spending_deviation: "📈",
                benfords_violation: "🔬", unusual_account_combo: "⚠️",
                vendor_concentration: "🏢", manual: "✏️",
            };
            for (const a of alerts) {
                const t = a.alert_type || "manual";
                typeMap[t] = (typeMap[t] || 0) + 1;
            }
            const maxType = Math.max(...Object.values(typeMap), 1);
            this.state.byType = Object.entries(typeMap)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8)
                .map(([key, count]) => ({
                    key,
                    label: typeLabels[key] || key,
                    icon: typeIcons[key] || "❓",
                    count,
                    pct: Math.round((count / maxType) * 100),
                }));

            // Recent alerts – top 20 open/critical/high
            this.state.recentAlerts = alerts
                .filter(a => ["open", "investigating", "escalated"].includes(a.state))
                .slice(0, 15)
                .map(a => ({
                    id: a.id,
                    title: a.title,
                    risk_level: a.risk_level,
                    alert_type: typeLabels[a.alert_type] || a.alert_type,
                    state: a.state,
                    anomaly_score: a.anomaly_score,
                    partner: a.partner_id ? a.partner_id[1] : "",
                    move: a.move_id ? a.move_id[1] : "",
                    detected_date: a.detected_date
                        ? new Date(a.detected_date).toLocaleDateString()
                        : "",
                }));

            this.state.lastUpdated = new Date().toLocaleTimeString();
        } finally {
            this.state.loading = false;
        }
    }

    async onRefresh() {
        await this._loadDashboardData();
    }

    openAlerts(domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Anomaly Alerts",
            res_model: "account.anomaly.alert",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: {},
        });
    }

    openAlert(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Alert Detail",
            res_model: "account.anomaly.alert",
            res_id: id,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: {},
        });
    }

    openCritical() { this.openAlerts([["risk_level", "=", "critical"]]); }
    openHigh() { this.openAlerts([["risk_level", "=", "high"]]); }
    openOpen() { this.openAlerts([["state", "=", "open"]]); }
    openEscalated() { this.openAlerts([["state", "=", "escalated"]]); }
    openAll() { this.openAlerts([]); }

    riskBadgeClass(risk) {
        return {
            critical: "ad-badge-critical",
            high: "ad-badge-high",
            medium: "ad-badge-medium",
            low: "ad-badge-low",
        }[risk] || "ad-badge-low";
    }

    stateBadgeClass(state) {
        return {
            open: "ad-state-open",
            investigating: "ad-state-investigating",
            escalated: "ad-state-escalated",
            resolved: "ad-state-resolved",
            false_positive: "ad-state-fp",
        }[state] || "";
    }

    scoreGradient(score) {
        if (score >= 80) return "#ef4444";
        if (score >= 60) return "#f97316";
        if (score >= 40) return "#eab308";
        return "#22c55e";
    }

    get criticalPct() {
        return this.state.kpi.total
            ? Math.round((this.state.kpi.critical / this.state.kpi.total) * 100)
            : 0;
    }
    get highPct() {
        return this.state.kpi.total
            ? Math.round((this.state.kpi.high / this.state.kpi.total) * 100)
            : 0;
    }
    get mediumPct() {
        return this.state.kpi.total
            ? Math.round((this.state.kpi.medium / this.state.kpi.total) * 100)
            : 0;
    }
    get lowPct() {
        return this.state.kpi.total
            ? Math.round((this.state.kpi.low / this.state.kpi.total) * 100)
            : 0;
    }
}

registry.category("actions").add(
    "account_anomaly_detector.anomaly_dashboard_action",
    AnomalyDashboard
);
