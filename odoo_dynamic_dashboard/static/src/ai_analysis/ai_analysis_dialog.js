import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { RPCError } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy, t, useProps } from "@odoo/owl";

const RECOMMENDATION_PREFIX = /^(\*\*)?[^:]{0,30}:\s*/;

/**
 * Split the answer of the AI in bullet points and its final recommendation.
 *
 * @param {string} text
 * @returns {{ points: string[], recommendation: string }}
 */
export function parseAnalysis(text) {
    const lines = (text || "")
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
    let recommendation = "";
    const last = lines.at(-1) || "";
    if (lines.length > 1 && !/^[-*•]/.test(last)) {
        // the AI is asked to end with "Recommendation: ...", possibly translated
        recommendation = last.replace(RECOMMENDATION_PREFIX, "");
        lines.pop();
    }
    const points = lines.map((line) => line.replace(/^[-*•]\s*/, "").replace(/\*\*/g, ""));
    return { points, recommendation: recommendation.replace(/\*\*/g, "") };
}

/**
 * Brief analysis of a dashboard block by Odoo's AI service, on the data shown to
 * the user (with the filters they applied to the block).
 */
export class BlockAiAnalysisDialog extends Component {
    static template = "odoo_dynamic_dashboard.BlockAiAnalysisDialog";
    static components = { Dialog };
    props = useProps({
        close: t.function(),
        block: t.object(),
        filterDomain: t.array(),
        filterSummary: t.string().optional(""),
        analysis: t.string().optional(""),
        onAnalyzed: t.function(),
    });

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.title = _t("AI Analysis: %s", this.props.block.name);
        this.state = proxy({ analysis: this.props.analysis, isLoading: false, error: false });
        onWillStart(() => {
            if (!this.state.analysis) {
                this.analyze();
            }
        });
    }

    getAnalysis() {
        return parseAnalysis(this.state.analysis);
    }

    async analyze() {
        this.state.isLoading = true;
        this.state.error = false;
        try {
            const { analysis } = await this.orm.silent.call(
                "dynamic.dashboard.block",
                "get_ai_analysis",
                [[this.props.block.id]],
                { filter_domain: this.props.filterDomain, filter_summary: this.props.filterSummary }
            );
            this.state.analysis = analysis;
            this.props.onAnalyzed(analysis);
        } catch (error) {
            if (!(error instanceof RPCError)) {
                throw error;
            }
            this.state.error = error.data?.message || _t("Sorry, the analysis could not be generated.");
        } finally {
            this.state.isLoading = false;
        }
    }

    async copy() {
        try {
            await browser.navigator.clipboard.writeText(this.state.analysis);
            this.notification.add(_t("Analysis copied to the clipboard."), { type: "success" });
        } catch {
            this.notification.add(_t("The analysis could not be copied."), { type: "warning" });
        }
    }
}
