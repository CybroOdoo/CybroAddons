/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

import { _t } from "@web/core/l10n/translation";
import { KpiCard } from "../components/kpi_card/kpi_card";
import { RevenueExpenseChart } from "../components/charts/revenue_expense_chart";
import { CashflowForecast } from "../components/charts/cashflow_forecast";
import { AgingChart } from "../components/charts/aging_chart";
import { TopExpensesChart } from "../components/charts/top_expenses_chart";
import { IncomeExpensePie } from "../components/charts/income_vs_expense_pie";
import { ProfitTrendChart } from "../components/charts/profit_trend_chart";
import { ExpenseBreakdownChart } from "../components/charts/expense_breakdown_chart";
import { BudgetVsActualChart } from "../components/charts/budget_vs_actual_chart";
import { MonthlyCashflowBars } from "../components/charts/monthly_cashflow_bars";
import { CashflowWaterfallChart } from "../components/charts/cashflow_waterfall_chart";
import { JournalBalanceChart } from "../components/charts/journal_balance_chart";
import { OverdueInvoices, UpcomingBills, RecentPayments } from "../components/lists/lists";
import { QuickActions, AlertsFeed } from "../components/quick_actions/action_buttons";

// Master KPI definitions
const KPI_DEFS = [
    {
        key: "invoices", title: "Invoices", icon: "fa-file-text-o", color: "blue", group: null, action: "view_invoices",
        info: "Total posted customer invoices in the selected period.\nFormula: SUM(posted out_invoice amounts)\nSource: account.move (move_type = out_invoice)"
    },
    {
        key: "bills", title: "Bills", icon: "fa-money", color: "orange", group: null, action: "view_bills",
        info: "Total posted vendor bills in the selected period.\nFormula: SUM(posted in_invoice amounts)\nSource: account.move (move_type = in_invoice)"
    },
    {
        key: "overdue_receivable", title: "Overdue Receivable", icon: "fa-exclamation-triangle", color: "red", group: null, action: "overdue_invoices",
        info: "Unpaid customer invoices past their due date.\nFormula: SUM(amount_residual) WHERE due_date < today\nSource: account.move (posted, not_paid/partial)"
    },
    {
        key: "overdue_payable", title: "Overdue Payable", icon: "fa-clock-o", color: "yellow", group: null, action: "overdue_bills",
        info: "Unpaid vendor bills past their due date.\nFormula: SUM(amount_residual) WHERE due_date < today\nSource: account.move (posted vendor bills)"
    },
    {
        key: "revenue", title: "Revenue", icon: "fa-line-chart", color: "green", group: "is_readonly", action: "revenue",
        info: "Total revenue from posted customer invoices (untaxed).\nFormula: SUM(amount_untaxed_signed) for out_invoices\nSource: account.move"
    },
    {
        key: "expenses", title: "Expenses", icon: "fa-arrow-down", color: "pink", group: "is_readonly", action: "expense",
        info: "Total expenses from posted vendor bills (untaxed).\nFormula: SUM(amount_untaxed_signed) for in_invoices\nSource: account.move"
    },
    {
        key: "net_profit", title: "Net Profit", icon: "fa-trophy", color: "green", group: "is_readonly",
        info: "Profit after subtracting expenses from revenue.\nFormula: Revenue − Expenses\nGreen if positive, red if negative."
    },
    {
        key: "cash_balance", title: "Cash Balance", icon: "fa-university", color: "indigo", group: "is_basic,is_readonly", action: "cash_balance",
        info: "Current balance across all bank and cash journals.\nFormula: SUM(balance) of posted entries in bank/cash accounts\nSource: account.move.line + account.journal"
    },
    {
        key: "total_receivable", title: "Total Receivable", icon: "fa-arrow-circle-down", color: "teal", group: "is_basic,is_readonly",
        info: "Total outstanding amount from all open customer invoices.\nFormula: SUM(amount_residual) for unpaid/partial out_invoices\nSource: account.move"
    },
    {
        key: "total_payable", title: "Total Payable", icon: "fa-arrow-circle-up", color: "orange", group: "is_basic,is_readonly", action: "total_payable",
        info: "Total outstanding amount owed to vendors.\nFormula: SUM(amount_residual) for unpaid/partial in_invoices\nSource: account.move"
    },
    {
        key: "net_cash_position", title: "Net Cash Position", icon: "fa-balance-scale", color: "cyan", group: "is_basic,is_readonly",
        info: "Cash available after paying all current liabilities.\nFormula: Cash Balance − Total Payable\nGreen if positive, red if negative."
    },
    {
        key: "working_capital", title: "Working Capital", icon: "fa-cogs", color: "teal", group: "is_basic,is_readonly",
        info: "Short-term financial health indicator.\nFormula: Total Receivable + Cash Balance − Total Payable\nMeasures ability to cover short-term obligations."
    },
    {
        key: "gross_margin", title: "Gross Margin", icon: "fa-percent", color: "green", group: "is_basic,is_readonly", useRaw: true, rawSuffix: "%",
        info: "Gross Margin Percentage — profitability before overhead.\nFormula: (Revenue − Expenses) ÷ Revenue × 100\nHigher is better. Compared as percentage-point change."
    },
    {
        key: "dso", title: "DSO", icon: "fa-calendar-check-o", color: "blue", group: "is_basic,is_readonly", useRaw: true, rawSuffix: " days",
        info: "Days Sales Outstanding — how fast customers pay.\nFormula: (Total Receivable ÷ Revenue) × Period Days\nLower is better. Industry avg: 30–45 days."
    },
    {
        key: "dpo", title: "DPO", icon: "fa-calendar-minus-o", color: "orange", group: "is_basic,is_readonly", useRaw: true, rawSuffix: " days",
        info: "Days Payables Outstanding — how fast you pay vendors.\nFormula: (Total Payable ÷ Expenses) × Period Days\nHigher means better cash retention, but watch relationships."
    },
    {
        key: "cash_burn_rate", title: "Daily Burn Rate", icon: "fa-fire", color: "pink", group: "is_basic,is_readonly",
        info: "Average daily spending rate.\nFormula: Total Expenses ÷ Number of Days in Period\nUsed to calculate Runway Days."
    },
    {
        key: "runway_days", title: "Runway", icon: "fa-road", color: "purple", group: "is_basic,is_readonly", useRaw: true, rawSuffix: " days",
        info: "Days of cash remaining at current burn rate.\nFormula: Cash Balance ÷ Daily Burn Rate\nCritical for cash planning. Below 90 days = high risk."
    },
];

// Master Chart definitions
const CHART_DEFS = [
    {
        key: "revenue_expense", title: "Revenue vs Expenses", icon: "fa-line-chart", component: "RevenueExpenseChart", dataKey: "chartData", group: "is_readonly",
        info: "Monthly comparison of revenue (invoices) and expenses (bills) over the selected period. Shows trends in profitability."
    },
    {
        key: "cashflow_forecast", title: "Cash Flow Forecast", icon: "fa-area-chart", component: "CashflowForecast", dataKey: "cashflowData", group: "is_readonly",
        info: "90-day forward projection of cash position based on open invoices, pending bills, and recurring patterns."
    },
    {
        key: "aging", title: "Aging Analysis", icon: "fa-bar-chart", component: "AgingChart", dataKey: "_aging", group: "is_basic,is_readonly",
        info: "Receivable and payable balances grouped by aging buckets: Current, 1–30, 31–60, 61–90, 90+ days. Helps identify collection risks."
    },
    {
        key: "profit_trend", title: "P&L Trend (12mo)", icon: "fa-line-chart", component: "ProfitTrendChart", dataKey: "profitTrend", group: "is_user,is_manager",
        info: "12-month rolling Profit & Loss trend. Shows Revenue, Expenses, and Net Profit lines. Data: posted account.move entries."
    },
    {
        key: "monthly_cashflow", title: "Cash Inflow / Outflow", icon: "fa-exchange", component: "MonthlyCashflowBars", dataKey: "monthlyCashflow", group: "is_readonly",
        info: "Monthly stacked bars showing cash inflows (customer payments) and outflows (vendor payments). Data: account.payment records."
    },
    {
        key: "top_expenses", title: "Top Expenses", icon: "fa-pie-chart", component: "TopExpensesChart", dataKey: "topExpenses", group: "is_readonly",
        info: "Top expense categories by amount in the selected period. Helps identify biggest cost drivers."
    },
    {
        key: "expense_breakdown", title: "Expense Breakdown", icon: "fa-pie-chart", component: "ExpenseBreakdownChart", dataKey: "expenseBreakdown", group: "is_readonly",
        info: "Doughnut chart of expenses grouped by account name. Shows proportion of each expense category."
    },
    {
        key: "income_expense_pie", title: "Income vs Expense", icon: "fa-pie-chart", component: "IncomeExpensePie", dataKey: "_pie", group: "is_readonly",
        info: "Simple pie showing the ratio of total income to total expenses. Quick visual indicator of profitability."
    },
    {
        key: "budget_vs_actual", title: "Budget vs Actual", icon: "fa-bar-chart", component: "BudgetVsActualChart", dataKey: "budgetVsActual", group: "is_readonly",
        info: "Compares budgeted amounts vs actual spending per budget line. Requires the Budget module (account_budget)."
    },
    {
        key: "cashflow_waterfall", title: "Cashflow Waterfall", icon: "fa-bar-chart", component: "CashflowWaterfallChart", dataKey: "cashflowWaterfall", group: "is_readonly",
        info: "Waterfall chart: Opening Cash → +Inflows → −Outflows → Closing Cash. Visual summary of where cash went during the period."
    },
];

export class AccountingDashboard extends Component {
    static template = "accounting_dashboard_pro.AccountingDashboard";
    static components = {
        KpiCard,
        RevenueExpenseChart,
        CashflowForecast,
        AgingChart,
        TopExpensesChart,
        IncomeExpensePie,
        ProfitTrendChart,
        ExpenseBreakdownChart,
        BudgetVsActualChart,
        MonthlyCashflowBars,
        CashflowWaterfallChart,
        JournalBalanceChart,
        OverdueInvoices,
        UpcomingBills,
        RecentPayments,
        QuickActions,
        AlertsFeed,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.companyService = useService("company");

        this.state = useState({
            loading: true,
            period: "this_month",
            amountFormat: "full",
            theme: "dark",
            date_from: null,
            date_to: null,
            kpiData: {},
            chartData: {},
            cashflowData: {},
            agingReceivable: {},
            agingPayable: {},
            listsData: {},
            alerts: [],
            topExpenses: {},
            taxSummary: {},
            profitTrend: {},
            expenseBreakdown: {},
            budgetVsActual: {},
            monthlyCashflow: {},
            cashflowWaterfall: {},
            journalCharts: [],
            chartInfoKey: null,
            userGroups: {},
            error: null,
            showKpiSettings: false,
            hiddenKpis: [],
            kpiOrder: [],
            hiddenCharts: [],
            account_journal_ids: [],
            chartOrder: [],
            settingsTab: "kpis",
            configId: null,
            showReportModal: false,
            availableReports: [],
            searchReportQuery: "",
        });

        this.allChartDefs = CHART_DEFS;

        this.periodOptions = [
            { value: "this_month", label: "This Month" },
            { value: "last_month", label: "Last Month" },
            { value: "this_quarter", label: "This Quarter" },
            { value: "last_quarter", label: "Last Quarter" },
            { value: "this_year", label: "This Year" },
            { value: "last_year", label: "Last Year" },
        ];

        this.formatOptions = [
            { value: "full", label: "Full" },
            { value: "K", label: "K" },
            { value: "M", label: "M" },
            { value: "B", label: "B" },
        ];

        this.allKpiDefs = KPI_DEFS;

        onWillStart(async () => {
            await this._loadConfig();
            await this.loadDashboardData();
        });
    }

    // -- Config persistence --

    async _loadConfig() {
        try {
            const config = await this.orm.call(
                "account.dashboard.config", "get_or_create_config", []
            );
            this.state.configId = config.id;
            this.state.theme = config.theme || "dark";
            this.state.amountFormat = config.amount_format || "full";
            this.state.hiddenKpis = config.hidden_kpis || [];
            this.state.kpiOrder = config.kpi_order || [];
            this.state.hiddenCharts = config.hidden_charts || [];
            this.state.chartOrder = config.chart_order || [];
            if (config.default_period) {
                this.state.period = config.default_period;
            }
        } catch (e) {
            console.error("Config load error:", e);
        }
    }

    async _saveConfig(vals) {
        if (!this.state.configId) return;
        try {
            await this.orm.call(
                "account.dashboard.config", "save_config",
                [[this.state.configId], vals]
            );
        } catch (e) {
            console.error("Config save error:", e);
        }
    }

    // -- Theme --

    get themeClass() {
        return this.state.theme === "dark" ? "adp-dark" : "adp-light";
    }

    get themeIcon() {
        return this.state.theme === "dark" ? "fa-moon-o" : "fa-sun-o";
    }

    toggleTheme() {
        this.state.theme = this.state.theme === "dark" ? "light" : "dark";
        this._saveConfig({ theme: this.state.theme });
    }

    // -- Format dropdown --

    onFormatChange(ev) {
        this.state.amountFormat = ev.target.value;
        this._saveConfig({ amount_format: this.state.amountFormat });
    }

    // -- Params --

    get params() {
        return {
            period: this.state.period,
            date_from: this.state.date_from,
            date_to: this.state.date_to,
            company_ids: this.companyService.activeCompanyIds,
        };
    }

    // -- Data loading --

    async loadDashboardData() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const [kpiData, listsData, alerts, account_journal_ids] = await Promise.all([
                this.orm.call("account.move", "get_dashboard_kpi_data", [this.params]),
                this.orm.call("account.move", "get_dashboard_lists", [this.params]),
                this.orm.call("account.move", "get_dashboard_alerts", [this.params]),
                this.orm.call("account.move", "get_account_journal_ids", [this.params]),
            ]);

            this.state.kpiData = kpiData;
            this.state.userGroups = kpiData.user_groups || {};
            this.state.listsData = listsData;
            this.state.alerts = alerts;
            this.state.account_journal_ids = account_journal_ids
            // Always load charts — visibleCharts getter handles group filtering
            await this._loadCharts();
        } catch (e) {
            console.error("Dashboard load error:", e);
            this.state.error = e.message || "Failed to load dashboard data";
        }
        this.state.loading = false;
    }

    async _loadCharts() {
        // Load each chart independently so one failure doesn't break all
        const safeCall = async (method, args, stateKey) => {
            try {
                this.state[stateKey] = await this.orm.call("account.move", method, [args]);
            } catch (e) {
                console.warn(`Chart ${stateKey} load failed:`, e.message || e);
            }
        };

        await Promise.all([
            safeCall("get_dashboard_chart_data", this.params, "chartData"),
            safeCall("get_dashboard_cashflow", { ...this.params, days: 90 }, "cashflowData"),
            safeCall("get_dashboard_aging", { ...this.params, type: "receivable" }, "agingReceivable"),
            safeCall("get_dashboard_aging", { ...this.params, type: "payable" }, "agingPayable"),
            safeCall("get_dashboard_top_expenses", this.params, "topExpenses"),
            safeCall("get_dashboard_tax_summary", this.params, "taxSummary"),
            safeCall("get_dashboard_profit_trend", this.params, "profitTrend"),
            safeCall("get_dashboard_expense_breakdown", this.params, "expenseBreakdown"),
            safeCall("get_dashboard_budget_vs_actual", this.params, "budgetVsActual"),
            safeCall("get_dashboard_monthly_cashflow_bars", this.params, "monthlyCashflow"),
            safeCall("get_dashboard_cashflow_waterfall", this.params, "cashflowWaterfall"),
            safeCall("get_dashboard_journal_balances", this.params, "journalCharts"),
        ]);
    }

    _hasGroupAccess(groupStr) {
        if (!groupStr) return true;
        const requiredGroups = groupStr.split(",");
        return requiredGroups.some(g => this.state.userGroups[g.trim()]);
    }

    // -- KPI management --

    get visibleKpis() {
        const groups = this.state.userGroups;
        const hidden = new Set(this.state.hiddenKpis);
        const order = this.state.kpiOrder;

        // Filter by access + not hidden
        let kpis = this.allKpiDefs.filter((k) => {
            if (hidden.has(k.key)) return false;
            if (!this._hasGroupAccess(k.group)) return false;
            return true;
        });

        // Sort by custom order if defined
        if (order.length) {
            const orderMap = {};
            order.forEach((key, idx) => (orderMap[key] = idx));
            kpis.sort((a, b) => {
                const ia = orderMap[a.key] !== undefined ? orderMap[a.key] : 999;
                const ib = orderMap[b.key] !== undefined ? orderMap[b.key] : 999;
                return ia - ib;
            });
        }

        return kpis;
    }

    get settingsKpis() {
        const groups = this.state.userGroups;
        const hidden = new Set(this.state.hiddenKpis);
        const order = this.state.kpiOrder;

        let kpis = this.allKpiDefs
            .filter((k) => this._hasGroupAccess(k.group))
            .map((k) => ({
                ...k,
                visible: !hidden.has(k.key),
            }));

        if (order.length) {
            const orderMap = {};
            order.forEach((key, idx) => (orderMap[key] = idx));
            kpis.sort((a, b) => {
                const ia = orderMap[a.key] !== undefined ? orderMap[a.key] : 999;
                const ib = orderMap[b.key] !== undefined ? orderMap[b.key] : 999;
                return ia - ib;
            });
        }

        return kpis;
    }

    getKpiAmount(kpi) {
        const data = this.state.kpiData[kpi.key];
        if (!data) return 0;
        if (kpi.key === "invoices" || kpi.key === "bills") return data.posted_amount || 0;
        return data.amount || 0;
    }

    getKpiSubtitle(kpi) {
        const data = this.state.kpiData[kpi.key];
        if (!data) return "";
        if (kpi.key === "invoices") return `${data.posted_count || 0} posted, ${data.draft_count || 0} draft`;
        if (kpi.key === "bills") return `${data.posted_count || 0} posted, ${data.draft_count || 0} draft`;
        if (kpi.key === "overdue_receivable") return `${data.count || 0} invoices overdue`;
        if (kpi.key === "overdue_payable") return `${data.count || 0} bills overdue`;
        if (kpi.key === "total_receivable") return "All open invoices";
        if (kpi.key === "total_payable") return "All open bills";
        if (kpi.key === "net_cash_position") return "Cash − Payables";
        if (kpi.key === "working_capital") return "Receivable + Cash − Payable";
        if (kpi.key === "gross_margin") return "(Revenue − Costs) / Revenue";
        if (kpi.key === "dso") return "Avg collection period";
        if (kpi.key === "dpo") return "Avg payment period";
        if (kpi.key === "cash_burn_rate") return "Avg daily spend";
        if (kpi.key === "runway_days") return "Days of cash left";
        return "";
    }

    getKpiChangePct(kpi) {
        const data = this.state.kpiData[kpi.key];
        return data?.change_pct || 0;
    }

    getKpiPrevAmount(kpi) {
        const data = this.state.kpiData[kpi.key];
        if (data?.prev_amount !== undefined) return data.prev_amount;
        return undefined;
    }

    getKpiColor(kpi) {
        if (kpi.key === "net_profit" || kpi.key === "net_cash_position" || kpi.key === "working_capital") {
            return this.getKpiAmount(kpi) >= 0 ? "green" : "red";
        }
        return kpi.color;
    }

    toggleKpiSettings() {
        this.state.showKpiSettings = !this.state.showKpiSettings;
    }

    closeKpiSettings() {
        this.state.showKpiSettings = false;
    }

    switchSettingsTab(tab) {
        this.state.settingsTab = tab;
    }

    // -- Chart management --

    get visibleCharts() {
        const groups = this.state.userGroups;
        const hidden = new Set(this.state.hiddenCharts);
        const order = this.state.chartOrder;

        let charts = this.allChartDefs.filter((c) => {
            if (hidden.has(c.key)) return false;
            if (!this._hasGroupAccess(c.group)) return false;
            return true;
        });

        if (order.length) {
            const orderMap = {};
            order.forEach((key, idx) => (orderMap[key] = idx));
            charts.sort((a, b) => {
                const ia = orderMap[a.key] !== undefined ? orderMap[a.key] : 999;
                const ib = orderMap[b.key] !== undefined ? orderMap[b.key] : 999;
                return ia - ib;
            });
        }

        return charts;
    }

    get settingsCharts() {
        const groups = this.state.userGroups;
        const hidden = new Set(this.state.hiddenCharts);
        const order = this.state.chartOrder;

        let charts = this.allChartDefs
            .filter((c) => this._hasGroupAccess(c.group))
            .map((c) => ({ ...c, visible: !hidden.has(c.key) }));

        if (order.length) {
            const orderMap = {};
            order.forEach((key, idx) => (orderMap[key] = idx));
            charts.sort((a, b) => {
                const ia = orderMap[a.key] !== undefined ? orderMap[a.key] : 999;
                const ib = orderMap[b.key] !== undefined ? orderMap[b.key] : 999;
                return ia - ib;
            });
        }

        return charts;
    }

    getChartData(chart) {
        // Special cases for composite-data charts
        if (chart.dataKey === "_aging") {
            return null;  // AgingChart gets receivable+payable separately
        }
        if (chart.dataKey === "_pie") {
            return null;  // IncomeExpensePie gets revenue/expenses from KPI data
        }
        return this.state[chart.dataKey] || {};
    }

    getChartComponent(chart) {
        return this.constructor.components[chart.component];
    }

    toggleChartVisibility(key) {
        const hidden = [...this.state.hiddenCharts];
        const idx = hidden.indexOf(key);
        if (idx >= 0) {
            hidden.splice(idx, 1);
        } else {
            hidden.push(key);
        }
        this.state.hiddenCharts = hidden;
        this._saveConfig({ hidden_charts: hidden });
    }

    moveChartUp(key) {
        const order = this._getCurrentChartOrder();
        const idx = order.indexOf(key);
        if (idx > 0) {
            [order[idx - 1], order[idx]] = [order[idx], order[idx - 1]];
            this.state.chartOrder = [...order];
            this._saveConfig({ chart_order: order });
        }
    }

    moveChartDown(key) {
        const order = this._getCurrentChartOrder();
        const idx = order.indexOf(key);
        if (idx < order.length - 1) {
            [order[idx], order[idx + 1]] = [order[idx + 1], order[idx]];
            this.state.chartOrder = [...order];
            this._saveConfig({ chart_order: order });
        }
    }

    _getCurrentChartOrder() {
        if (this.state.chartOrder.length) {
            return [...this.state.chartOrder];
        }
        return this.settingsCharts.map((c) => c.key);
    }

    toggleKpiVisibility(key) {
        const hidden = [...this.state.hiddenKpis];
        const idx = hidden.indexOf(key);
        if (idx >= 0) {
            hidden.splice(idx, 1);
        } else {
            hidden.push(key);
        }
        this.state.hiddenKpis = hidden;
        this._saveConfig({ hidden_kpis: hidden });
    }

    moveKpiUp(key) {
        const order = this._getCurrentOrder();
        const idx = order.indexOf(key);
        if (idx > 0) {
            [order[idx - 1], order[idx]] = [order[idx], order[idx - 1]];
            this.state.kpiOrder = [...order];
            this._saveConfig({ kpi_order: order });
        }
    }

    moveKpiDown(key) {
        const order = this._getCurrentOrder();
        const idx = order.indexOf(key);
        if (idx < order.length - 1) {
            [order[idx], order[idx + 1]] = [order[idx + 1], order[idx]];
            this.state.kpiOrder = [...order];
            this._saveConfig({ kpi_order: order });
        }
    }

    _getCurrentOrder() {
        if (this.state.kpiOrder.length) {
            return [...this.state.kpiOrder];
        }
        return this.settingsKpis.map((k) => k.key);
    }

    // -- Period --

    async onPeriodChange(ev) {
        this.state.period = ev.target.value;
        this._saveConfig({ default_period: this.state.period });
        await this.loadDashboardData();
    }

    async onRefresh() {
        await this.loadDashboardData();
    }

    // -- Actions --

    _todayISO() {
        const today = new Date();
        const month = String(today.getMonth() + 1).padStart(2, "0");
        const day = String(today.getDate()).padStart(2, "0");
        return `${today.getFullYear()}-${month}-${day}`;
    }

    _computePeriodDates() {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth(); // 0-indexed
        const toISO = (dt) => {
            const m = String(dt.getMonth() + 1).padStart(2, "0");
            const d = String(dt.getDate()).padStart(2, "0");
            return `${dt.getFullYear()}-${m}-${d}`;
        };
        const endOfMonth = (y, m) => new Date(y, m + 1, 0);

        let dateFrom = null;
        let dateTo = null;

        switch (this.state.period) {
            case "this_month":
                dateFrom = new Date(year, month, 1);
                dateTo = now;
                break;
            case "last_month":
                dateFrom = new Date(year, month - 1, 1);
                dateTo = endOfMonth(year, month - 1);
                break;
            case "this_quarter": {
                const quarterStartMonth = Math.floor(month / 3) * 3;
                dateFrom = new Date(year, quarterStartMonth, 1);
                dateTo = now;
                break;
            }
            case "last_quarter": {
                const quarterStartMonth = Math.floor(month / 3) * 3;
                const lastQuarterEnd = new Date(year, quarterStartMonth, 0);
                const lastQuarterStartMonth = Math.floor(lastQuarterEnd.getMonth() / 3) * 3;
                dateFrom = new Date(lastQuarterEnd.getFullYear(), lastQuarterStartMonth, 1);
                dateTo = lastQuarterEnd;
                break;
            }
            case "this_year":
                dateFrom = new Date(year, 0, 1);
                dateTo = now;
                break;
            case "last_year":
                dateFrom = new Date(year - 1, 0, 1);
                dateTo = new Date(year - 1, 11, 31);
                break;
            default:
                break;
        }

        return {
            date_from: dateFrom ? toISO(dateFrom) : null,
            date_to: dateTo ? toISO(dateTo) : null,
        };
    }

    _getDashboardDateRange() {
        const serverPeriod = this.state.kpiData?.period || {};
        if (serverPeriod.date_from && serverPeriod.date_to) {
            return {
                date_from: serverPeriod.date_from,
                date_to: serverPeriod.date_to,
            };
        }
        return this._computePeriodDates();
    }

    _draftFilterDomain() {
        const domain = [];
        const activeCompanyIds = this.companyService.activeCompanyIds;
        if (activeCompanyIds.length) {
            domain.push(["company_id", "in", activeCompanyIds]);
        }
        return domain;
    }

    _buildFilterDomain(dateField = "date") {
        const domain = [];
        const activeCompanyIds = this.companyService.activeCompanyIds;
        if (activeCompanyIds.length) {
            domain.push(["company_id", "in", activeCompanyIds]);
        }

        const { date_from, date_to } = this._getDashboardDateRange();
        if (date_from) {
            domain.push([dateField, ">=", date_from]);
        }
        if (date_to) {
            domain.push([dateField, "<=", date_to]);
        }
        return domain;
    }

    _mergeDomain(baseDomain = [], dateField = "date") {
        return [...baseDomain, ...this._buildFilterDomain(dateField)];
    }

    _getDateBefore(days) {
        const d = new Date();
        d.setDate(d.getDate() - days);
        return d.toISOString().split("T")[0];
    }

    onAction(actionName, smart = false) {
        const today = this._todayISO();

        const actionMap = {
            new_invoice: {
                type: "ir.actions.act_window",
                res_model: "account.move",
                view_mode: "form",
                views: [[false, "form"]],
                context: { default_move_type: "out_invoice" },
            },
            new_bill: {
                type: "ir.actions.act_window",
                res_model: "account.move",
                view_mode: "form",
                views: [[false, "form"]],
                context: { default_move_type: "in_invoice" },
            },
            journal_entry: {
                type: "ir.actions.act_window",
                name: _t("Journal Entries"),
                res_model: "account.move",
                view_mode: "form",
                views: [[false, "form"]],
                context: { 'default_move_type': 'entry', 'search_default_posted': 1, 'view_no_maturity': true },
            },
            reconciliation: {
                type: "ir.actions.act_window",
                name: _t("Bank Matching"),
                res_model: "account.bank.statement.line",
                view_mode: "kanban,list",
                views: [[false, "kanban"], [false, "list"]],
                domain: [['state', '!=', 'cancel']],
            },
            lock_date: {
                type: "ir.actions.act_window",
                name: _t("Lock Journal Entries"),
                res_model: "account.change.lock.date",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
            },
            new_payment: {
                type: "ir.actions.act_window",
                res_model: "account.payment",
                view_mode: "form",
                views: [[false, "form"]],
            },
            view_invoices: {
                type: "ir.actions.act_window",
                name: "Customer Invoices",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"], [false, "pivot"]],
                domain: this._mergeDomain([["move_type", "=", "out_invoice"], ["state", "=", "posted"]]),
            },

            expense: {
                type: "ir.actions.act_window",
                name: "Expenses",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"], [false, "pivot"]],
                domain: this._mergeDomain([["move_type", "in", ['in_invoice']], ["state", "=", "posted"]]),
            },

            revenue: {
                type: "ir.actions.act_window",
                name: "Revenue",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"], [false, "pivot"]],
                domain: this._mergeDomain([["move_type", "in", ['out_invoice']], ["state", "=", "posted"]]),
            },

            view_bills: {
                type: "ir.actions.act_window",
                name: "Vendor Bills",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"], [false, "pivot"]],
                domain: this._mergeDomain([["move_type", "=", "in_invoice"], ["state", "=", "posted"]]),
            },
            cash_balance: {
                type: "ir.actions.act_window",
                name: "Cash Balance",
                res_model: "account.move.line",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"], [false, "pivot"]],
                domain: this._mergeDomain([["parent_state", "=", "posted"], ["account_id", "in", this.state.account_journal_ids]]),
            },
            overdue_invoices: {
                type: "ir.actions.act_window",
                name: "Overdue Invoices",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"]],
                domain: smart ? [["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["payment_state", "in", ["not_paid", "partial"]],
                ["invoice_date_due", "<", today], ...this._draftFilterDomain()] : this._mergeDomain([
                    ["move_type", "=", "out_invoice"],
                    ["state", "=", "posted"],
                    ["payment_state", "in", ["not_paid", "partial"]],
                    ["invoice_date_due", "<", today],
                ], "date"),
            },
            overdue_bills: {
                type: "ir.actions.act_window",
                name: "Overdue Bills",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"]],
                domain: this._mergeDomain([
                    ["move_type", "=", "in_invoice"],
                    ["state", "=", "posted"],
                    ["payment_state", "in", ["not_paid", "partial"]],
                    ["invoice_date_due", "<", today],
                ], "date"),
            },
            reconcile: {
                type: "ir.actions.act_window",
                name: "Unreconciled Transactions",
                res_model: "account.bank.statement.line",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"]],

                domain: smart ? [["is_reconciled", "=", false], ...this._draftFilterDomain()] : this._mergeDomain([["is_reconciled", "=", false]]),
                context: { create: false },
            },
            bills_due_today: {
                type: "ir.actions.act_window",
                name: "Bills Due Today",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["move_type", "=", "in_invoice"],
                    ["state", "=", "posted"],
                    ["payment_state", "in", ["not_paid", "partial"]],
                    ["invoice_date_due", "=", today]]
            },
            draft_moves: {
                type: "ir.actions.act_window",
                name: "Draft Invoices & Bills",
                res_model: "account.move",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["state", "=", "draft"],
                    ["move_type", "in", ["out_invoice", "in_invoice"]],
                    ...this._draftFilterDomain(),
                ],
            },
            generate_reports: {
                type: "ir.actions.client",
                tag: "account_report",
                name: "Financial Reports",
            },
            configure_settings: {
                type: "ir.actions.act_window",
                name: "Configure Settings",
                res_model: "res.config.settings",
                view_mode: "form",
                views: [[false, "form"]],
                target: "inline",
                context: { module: "account" },
            },
            export_all_data: {
                type: "ir.actions.act_window",
                name: "Export Financial Data",
                res_model: "account.move",
                view_mode: "list",
                views: [[false, "list"]],
            },
        };

        if (actionName === 'generate_reports') {
            if (!registry.category("actions").contains("account_report")) {
                this.env.services.notification?.add(_t("Accounting Reports module is not installed."), { type: "danger" });
                return;
            }
            if (!this.state.userGroups.is_user && !this.state.userGroups.is_manager) {
                console.warn("Unauthorized report access attempt.");
                return;
            }
            this.onGenerateReportsClick();
            return;
        }

        if (actionName === 'total_payable') {
            (async () => {
                try {
                    const resId = await this.orm.call("ir.model.data", "_xmlid_to_res_id", ["account_reports.aged_payable_report"]);
                    if (resId && registry.category("actions").contains("account_report")) {
                        this.action.doAction({
                            type: "ir.actions.client",
                            tag: "account_report",
                            name: "Aged Payable",
                            context: { report_id: resId }
                        });
                    } else {
                        // Fallback to vendor bills view
                        this.action.doAction({
                            type: "ir.actions.act_window",
                            name: "Total Payable",
                            res_model: "account.move",
                            view_mode: "list,form",
                            views: [[false, "list"], [false, "form"], [false, "pivot"]],
                            domain: this._mergeDomain([["move_type", "=", "in_invoice"], ["state", "=", "posted"], ["payment_state", "in", ["not_paid", "partial"]]]),
                        });
                    }
                } catch (e) {
                    console.warn("Failed to resolve Aged Payable report via XML ID, fallback to report_id 9:", e);
                    if (registry.category("actions").contains("account_report")) {
                        this.action.doAction({
                            type: "ir.actions.client",
                            tag: "account_report",
                            name: "Aged Payable",
                            context: { report_id: 9 }
                        });
                    } else {
                        this.action.doAction({
                            type: "ir.actions.act_window",
                            name: "Total Payable",
                            res_model: "account.move",
                            view_mode: "list,form",
                            views: [[false, "list"], [false, "form"], [false, "pivot"]],
                            domain: this._mergeDomain([["move_type", "=", "in_invoice"], ["state", "=", "posted"], ["payment_state", "in", ["not_paid", "partial"]]]),
                        });
                    }
                }
            })();
            return;
        }

        if (actionMap[actionName]) {
            this.action.doAction(actionMap[actionName]);
        }
    }

    async onGenerateReportsClick() {
        if (!this.state.availableReports || this.state.availableReports.length === 0) {
            try {
                const reports = await this.orm.searchRead("account.report", [], ["id", "name"]);
                this.state.availableReports = reports || [];
            } catch (e) {
                console.error("Failed to load accounting reports:", e);
            }
        }
        this.state.showReportModal = true;
    }

    get filteredReports() {
        const query = (this.state.searchReportQuery || "").toLowerCase().trim();
        if (!query) {
            return this.state.availableReports || [];
        }
        return (this.state.availableReports || []).filter(r =>
            (r.name || "").toLowerCase().includes(query)
        );
    }

    openReport(reportId, reportName) {
            this.state.showReportModal = false;
            if (!registry.category("actions").contains("account_report")) {
                this.env.services.notification?.add(_t("Accounting Reports module is not installed."), { type: "danger" });
                return;
            }
            this.action.doAction({
                type: "ir.actions.client",
                tag: "account_report",
                name: reportName,
                context: { report_id: reportId }
            });
        }

    onKpiClick(actionName) {
        if (actionName) this.onAction(actionName);
    }

    onListItemClick(model, id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: id,
            view_mode: "form",
            views: [[false, "form"]],
        });
    }

    // -- Formatting --

    formatCurrency(amount) {
        if (amount === null || amount === undefined) return "—";
        const symbol = this.state.kpiData.currency_symbol || "$";
        const fmt = this.state.amountFormat;
        let formatted;

        const abs = Math.abs(amount);
        if (fmt === "B") {
            formatted = (abs / 1e9).toFixed(2) + "B";
        } else if (fmt === "M") {
            formatted = (abs / 1e6).toFixed(2) + "M";
        } else if (fmt === "K") {
            formatted = (abs / 1e3).toFixed(1) + "K";
        } else {
            formatted = abs.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
        }

        return amount < 0 ? `-${symbol} ${formatted}` : `${symbol} ${formatted}`;
    }

    formatCompact(amount) {
        if (Math.abs(amount) >= 1e9) return (amount / 1e9).toFixed(1) + "B";
        if (Math.abs(amount) >= 1e6) return (amount / 1e6).toFixed(1) + "M";
        if (Math.abs(amount) >= 1e3) return (amount / 1e3).toFixed(1) + "K";
        return amount.toFixed(0);
    }
}

registry.category("actions").add("accounting_dashboard_pro", AccountingDashboard);
