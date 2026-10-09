import { Component, proxy, t, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { formatFloat, formatInteger } from "@web/views/fields/formatters";

import { AiChartBlock, AiKpiBlock, AiTableBlock } from "./blocks";
import { renderMarkdown } from "./markdown";

export class AiChatMessage extends Component {
    static template = "ai_accounting_analytics.ChatMessage";
    static components = { AiChartBlock, AiKpiBlock, AiTableBlock };
    props = useProps({
        message: t.object(),
        streaming: t.boolean().optional(false),
        isLast: t.boolean().optional(false),
        userAvatar: t.string().optional(),
        onExport: t.function().optional(),
        onOpenRecord: t.function().optional(),
        onRetry: t.function().optional(),
    });

    setup() {
        this.state = proxy({ showSteps: false, copied: false });
    }

    html(text) {
        return renderMarkdown(text);
    }

    hasError() {
        return (this.props.message.parts || []).some((part) => part.type === "error");
    }

    workedFor() {
        const message = this.props.message;
        const seconds = Math.max(1, Math.round((message.duration_ms || 0) / 1000));
        const steps = (message.steps || []).length;
        const stepsLabel = steps === 1 ? _t("1 step") : _t("%s steps", steps);
        if (this.props.streaming) {
            return steps ? _t("Working… · %s", stepsLabel) : _t("Thinking…");
        }
        return steps
            ? _t("Worked for %(seconds)ss · %(steps)s", { seconds, steps: stepsLabel })
            : _t("Answered in %ss", seconds);
    }

    statusIcon() {
        if (this.props.streaming) {
            return "progress_activity";
        }
        return this.hasError() ? "error" : "check_circle";
    }

    tokens() {
        const message = this.props.message;
        return formatInteger((message.input_tokens || 0) + (message.output_tokens || 0));
    }

    cost() {
        return `$${formatFloat(this.props.message.cost || 0, { digits: [16, 4] })}`;
    }

    exportBlock(index, format) {
        this.props.onExport?.(this.props.message.id, index, format);
    }

    retry() {
        this.props.onRetry?.(this.props.message);
    }

    async copy() {
        await navigator.clipboard.writeText(this.props.message.content || "");
        this.state.copied = true;
        setTimeout(() => (this.state.copied = false), 1500);
    }
}
