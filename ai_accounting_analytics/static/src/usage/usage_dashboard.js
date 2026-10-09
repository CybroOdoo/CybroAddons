import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { deserializeDateTime, formatDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { humanNumber } from "@web/core/utils/numbers";
import { useService } from "@web/core/utils/hooks";
import { formatFloat, formatInteger } from "@web/views/fields/formatters";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

import { AiChartBlock, formatChartValue } from "../chat/blocks";

const PERIODS = [
    { key: "this_month", label: _t("This month") },
    { key: "last_month", label: _t("Last month") },
    { key: "last_30_days", label: _t("30 days") },
    { key: "this_year", label: _t("This year") },
    { key: "all_time", label: _t("All time") },
];

const TOKEN_TYPES = {
    input_tokens: _t("Input"),
    cached_tokens: _t("Cached input"),
    cache_write_tokens: _t("Cache writes"),
    output_tokens: _t("Output"),
};

/** AI Usage & Cost: what the AI calls cost, per period, model and user. */
export class AiUsageDashboard extends Component {
    static template = "ai_accounting_analytics.UsageDashboard";
    static components = { AiChartBlock };
    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.periods = PERIODS;
        this.state = proxy({ period: "this_month", data: null, loading: true });
        onWillStart(() => this.load());
    }

    async load(period = this.state.period) {
        this.state.loading = true;
        const data = await this.orm.call("ai.accounting.usage", "ai_get_dashboard", [period]);
        Object.assign(this.state, { period, data, loading: false });
    }

    // ------------------------------------------------------------------
    // Formatting
    // ------------------------------------------------------------------
    usd(value) {
        return formatChartValue(value || 0, { value_type: "usd" });
    }

    tokens(value) {
        return value >= 10000 ? humanNumber(value, { decimals: 1 }) : formatInteger(value || 0);
    }

    percent(value) {
        return `${formatFloat(value || 0, { digits: [16, 1] })} %`;
    }

    seconds(value) {
        return _t("%s s", formatFloat(value || 0, { digits: [16, 1] }));
    }

    date(value) {
        return formatDateTime(deserializeDateTime(value), { format: "d MMM, HH:mm" });
    }

    kpis() {
        const kpis = this.state.data.kpis;
        return [
            { key: "cost", label: _t("Total cost"), icon: "payments", value: this.usd(kpis.cost.value),
              delta: kpis.cost.delta },
            { key: "tokens", label: _t("Tokens"), icon: "database", value: this.tokens(kpis.tokens.value),
              delta: kpis.tokens.delta },
            { key: "answers", label: _t("Answers"), icon: "forum", value: formatInteger(kpis.answers.value),
              delta: kpis.answers.delta },
            { key: "cost_per_answer", label: _t("Cost per answer"), icon: "receipt_long",
              value: this.usd(kpis.cost_per_answer.value), delta: kpis.cost_per_answer.delta },
        ];
    }

    insights() {
        const kpis = this.state.data.kpis;
        return [
            { label: _t("Saved by prompt caching"), icon: "attach_money", value: this.usd(kpis.cache_savings.value) },
            { label: _t("Input read from cache"), icon: "flash_on", value: this.percent(kpis.cache_rate.value) },
            { label: _t("AI time per answer"), icon: "schedule", value: this.seconds(kpis.seconds_per_answer.value) },
            { label: _t("AI calls"), icon: "swap_horiz", value: formatInteger(kpis.calls.value) },
        ];
    }

    stepsLabel(steps) {
        return steps === 1 ? _t("1 step") : _t("%s steps", steps);
    }

    deltaLabel(delta) {
        const sign = delta > 0 ? "+" : "";
        return `${sign}${formatFloat(delta, { digits: [16, 1] })} %`;
    }

    // ------------------------------------------------------------------
    // Charts
    // ------------------------------------------------------------------
    costChart() {
        const timeline = this.state.data.timeline;
        return {
            type: "chart",
            chart_type: "bar",
            value_type: "usd",
            title: timeline.granularity === "day" ? _t("Cost per day") : _t("Cost per month"),
            labels: timeline.labels,
            datasets: [{ label: String(_t("Cost")), data: timeline.cost }],
        };
    }

    tokenChart() {
        const timeline = this.state.data.timeline;
        return {
            type: "chart",
            chart_type: "line",
            value_type: "number",
            title: timeline.granularity === "day" ? _t("Tokens per day") : _t("Tokens per month"),
            labels: timeline.labels,
            datasets: [{ label: String(_t("Tokens")), data: timeline.tokens }],
        };
    }

    modelChart() {
        const models = this.state.data.by_model;
        return {
            type: "chart",
            chart_type: "pie",
            value_type: "usd",
            title: _t("Cost by model"),
            labels: models.map((model) => model.name),
            datasets: [{ label: String(_t("Cost")), data: models.map((model) => model.cost) }],
        };
    }

    mixChart() {
        const mix = this.state.data.token_mix.filter((item) => item.value);
        return {
            type: "chart",
            chart_type: "pie",
            value_type: "number",
            title: _t("Token mix"),
            // Chart.js needs plain strings, not lazy translations.
            labels: mix.map((item) => String(TOKEN_TYPES[item.key])),
            datasets: [{ label: String(_t("Tokens")), data: mix.map((item) => item.value) }],
        };
    }

    hasTokens() {
        return this.state.data.token_mix.some((item) => item.value);
    }

    // ------------------------------------------------------------------
    // Actions
    // ------------------------------------------------------------------
    setPeriod(period) {
        if (period !== this.state.period) {
            this.load(period);
        }
    }

    openDetails() {
        this.actionService.doAction("ai_accounting_analytics.ai_accounting_usage_action");
    }

    openChat(chatId) {
        this.actionService.doAction("ai_accounting_analytics.ai_accounting_chat_action_client", {
            additionalContext: chatId ? { ai_chat_id: chatId } : {},
        });
    }
}

registry.category("actions").add("ai_accounting_analytics.usage_dashboard", AiUsageDashboard);
