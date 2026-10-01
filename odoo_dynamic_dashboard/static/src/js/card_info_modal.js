/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { Component, onMounted, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

export class CardInfoModal extends Component {
    static template = "CardInfoModal";
    static components = { Dialog };
    static props = {
        card: Object,
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.title = _t("Card Insights");
        this.themeMode = this._detectThemeMode();
        this.state = useState({
            loading: true,
            analysis: "",
            error: null,
        });

        onMounted(() => {
            this.runAnalysis();
        });
    }

    _detectThemeMode() {
        const dashboard = document.querySelector(".ad_dashboard");
        if (!dashboard) return "light";
        if (dashboard.classList.contains("dark-mode")) return "dark";
        if (dashboard.classList.contains("ocean-breeze-mode")) return "ocean";
        if (dashboard.classList.contains("cyberpunk-mode")) return "cyberpunk";
        return "light";
    }

    get contentClass() {
        return `card-info-modal-wrapper theme-${this.themeMode}`;
    }

    get card() {
        return this.props.card;
    }

    async runAnalysis() {
        this.state.loading = true;
        this.state.error = null;
        this.state.analysis = "";
        try {
            const result = await this.orm.call(
                "dashboard.card",
                "analyze_card_with_ai",
                [this.props.card.id]
            );
            this.state.analysis = (result || "").trim();
            if (!this.state.analysis) {
                this.state.error = _t("AI returned an empty response.");
            }
        } catch (e) {
            this.state.error = e?.data?.message || e?.message || _t("Unable to analyze this card.");
        } finally {
            this.state.loading = false;
        }
    }

    get sections() {
        const text = this.state.analysis;
        if (!text) return [];
        const headings = ["PURPOSE", "KEY INSIGHTS", "RECOMMENDATIONS"];
        const sections = [];
        const pattern = new RegExp(`^(${headings.join("|")})\\s*$`, "im");
        const lines = text.split(/\r?\n/);
        let current = null;
        for (const raw of lines) {
            const line = raw.trim();
            if (!line) continue;
            const m = line.match(pattern);
            if (m) {
                if (current) sections.push(current);
                current = { title: this._titleCase(m[1]), body: [] };
            } else if (current) {
                current.body.push(line);
            }
        }
        if (current) sections.push(current);
        if (sections.length === 0) {
            return [{ title: _t("Analysis"), body: lines.filter(l => l.trim()) }];
        }
        return sections;
    }

    _titleCase(text) {
        return text.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
    }

    sectionIcon(title) {
        const t = (title || "").toLowerCase();
        if (t.includes("purpose")) return "fa-bullseye";
        if (t.includes("insight")) return "fa-lightbulb-o";
        if (t.includes("recommend")) return "fa-check-circle";
        return "fa-file-text-o";
    }

    isBullet(line) {
        return /^[-*•]\s+/.test(line);
    }

    cleanBullet(line) {
        return line.replace(/^[-*•]\s+/, "");
    }
}