import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("ai_accounting_analytics_chat_tour", {
    steps: () => [
        {
            content: "Accept the one-time data sharing notice",
            trigger: ".o_ai_accounting button:contains('I understand')",
            run: "click",
        },
        {
            content: "Type a question",
            trigger: ".o_ai_accounting_input:enabled",
            run: "edit Top customers this year",
        },
        {
            content: "Send it",
            trigger: ".o_ai_accounting_send:not(.o_ai_accounting_stop):enabled",
            run: "click",
        },
        {
            content: "The tool table is streamed",
            trigger: ".o_ai_accounting_table td:contains('partner_a')",
        },
        {
            content: "The answer text is rendered as markdown",
            trigger: ".o_ai_accounting_text strong:contains('partner_a')",
        },
        {
            content: "The conversation appears in the sidebar",
            trigger: ".o_ai_accounting_chat_active:contains('Top customers this year')",
        },
        {
            content: "The usage line is shown once done",
            trigger: ".o_ai_accounting span:contains('tokens')",
        },
        {
            content: "Ask a follow-up",
            trigger: ".o_ai_accounting_input:enabled",
            run: "edit And the overview with a sales chart?",
        },
        {
            content: "Send it",
            trigger: ".o_ai_accounting_send:not(.o_ai_accounting_stop):enabled",
            run: "click",
        },
        {
            content: "KPI cards are rendered",
            trigger: ".o_ai_accounting_kpi:contains('Net Profit')",
        },
        {
            content: "The chart canvas is rendered",
            trigger: ".o_ai_accounting_chart canvas",
        },
        {
            content: "Final answer",
            trigger: ".o_ai_accounting_text:contains('Sales are growing.')",
        },
        {
            content: "Steps can be expanded",
            trigger: ".o_ai_accounting button:contains('2 steps')",
            run: "click",
        },
        {
            content: "Steps list",
            trigger: ".o_ai_accounting li:contains('Key figures')",
        },
    ],
});
