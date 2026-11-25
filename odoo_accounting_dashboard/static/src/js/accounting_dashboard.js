/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, signal, proxy, onMounted, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

/**
 * Helper to safely extract DOM element from signal.ref() or standard ref object in Odoo 20.
 */
function getRefEl(ref) {
    if (!ref) return null;
    if (typeof ref === "function") return ref();
    return ref.el || ref.current || ref;
}

export class AccountDashboard extends Component {
    setup() {
        this.state = proxy({
            data: {},
            top: {},
            income_chart: {},
            chart: [],
            payment_data: [],
            top_sale_cust: [],
            IncomeExpense: 'income',
            top_filter: 'this_month',
            income: 'income_this_month',
            aged_filter: 'aged_receive',
            top_sale_cust_filter: 'this_month',
            aged_payable_filter: 'this_month',
            payment_data_filter: 'this_month',
            payment_list_filter: 'customer_payment',
        });
        this.All = signal.ref();
        this.AgedRecords = signal.ref();
        this.Balance = signal.ref();
        this.orm = useService("orm");

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.fetchData();
        });

        onMounted(() => {
            this.renderChart();
        });
    }

    async onIncomeExpenseChange(ev) {
        this.state.IncomeExpense = ev.target.value;
        await this.onPeriodChange();
    }

    async onIncomePeriodChange(ev) {
        this.state.income = ev.target.value;
        await this.onPeriodChange();
    }

    async onPaymentListFilterChange(ev) {
        this.state.payment_list_filter = ev.target.value;
        await this.onPeriodChange();
    }

    async onPaymentDataFilterChange(ev) {
        this.state.payment_data_filter = ev.target.value;
        await this.onPeriodChange();
    }

    async onAgedFilterChange(ev) {
        this.state.aged_filter = ev.target.value;
        await this.onPeriodChange();
    }

    async onAgedPayableFilterChange(ev) {
        this.state.aged_payable_filter = ev.target.value;
        await this.onPeriodChange();
    }

    async onTopSaleCustFilterChange(ev) {
        this.state.top_sale_cust_filter = ev.target.value;
        await this.onPeriodChange();
    }

    async onTopFilterChange(ev) {
        this.state.top_filter = ev.target.value;
        await this.onPeriodChange();
    }

    async onPeriodChange() {
        this.destroyCharts();
        await this.fetchAndRender();
    }

    destroyCharts() {
        if (this.state.chart && this.state.chart.length > 0) {
            this.state.chart.forEach((chart) => {
                try {
                    chart.destroy();
                } catch {
                    // Ignore already destroyed charts
                }
            });
            this.state.chart = [];
        }
    }

    async fetchAndRender() {
        await this.fetchData();
        this.renderChart();
    }

    async fetchData() {
        this.state.data = await this.orm.call('account.move', 'get_datas', []);
        this.state.income_chart = await this.orm.call("account.move", "get_income_chart", [this.state.income]);
        this.state.payment_data = await this.orm.call("account.move", "get_payment_data", [this.state.payment_list_filter, this.state.payment_data_filter]);
        this.state.top = await this.orm.call("account.move", "get_top_datas", [this.state.top_filter]);
        this.state.aged_payable = await this.orm.call("account.move", "get_aged_payable", [this.state.aged_filter, this.state.aged_payable_filter]);
        this.state.top_sale_cust = await this.orm.call("account.move", "get_sale_revenue", [this.state.top_sale_cust_filter]);
        this.state.balance = await this.orm.call("account.move", "get_bank_balance", []);
    }

    renderChart() {
        const agedEl = getRefEl(this.AgedRecords);
        const allEl = getRefEl(this.All);

        if (agedEl && this.state.aged_payable) {
            this.renderAgedChart(agedEl, 'bar', this.state.aged_payable.partner, 'Amount', this.state.aged_payable.amount);
        }

        if (allEl && this.state.income_chart) {
            if (this.state.IncomeExpense === 'income') {
                this.renderIncomeChart(allEl, 'bar', this.state.income_chart.date, this.state.income_chart.income);
            } else if (this.state.IncomeExpense === 'expense') {
                this.renderExpenseChart(allEl, 'bar', this.state.income_chart.date, this.state.income_chart.expense);
            } else if (this.state.IncomeExpense === 'profit') {
                this.renderProfitChart(allEl, 'line', this.state.income_chart.date, this.state.income_chart.profit);
            } else {
                this.renderAllInOneChart(allEl, 'bar', this.state.income_chart.date, this.state.income_chart.income, this.state.income_chart.expense, this.state.income_chart.profit);
            }
        }
    }

    createChart(canvas, config) {
        if (!canvas) return;
        const ChartClass = window.Chart || Chart;
        if (ChartClass && ChartClass.getChart) {
            const existing = ChartClass.getChart(canvas);
            if (existing) {
                existing.destroy();
            }
        }
        const chartInstance = new ChartClass(canvas, config);
        this.state.chart.push(chartInstance);
        return chartInstance;
    }

    renderAgedChart(canvas, type, labels, label, data) {
        if (!canvas) return;
        this.createChart(canvas, {
            type: type,
            data: {
                labels: labels,
                datasets: [
                    {
                        label: label,
                        data: data,
                        borderRadius: 10,
                        backgroundColor: 'rgba(39, 232, 232, 0.5)',
                        borderColor: 'rgba(39, 232, 232, 1)',
                    }
                ]
            },
        });
    }

    renderIncomeChart(canvas, type, labels, data) {
        if (!canvas) return;
        this.createChart(canvas, {
            type: type,
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Income',
                        data: data,
                        borderWidth: 2,
                        borderRadius: 10,
                        borderSkipped: false,
                        backgroundColor: 'rgba(39, 232, 232, 0.5)',
                        borderColor: 'rgba(39, 232, 232, 1)',
                    },
                ]
            },
        });
    }

    renderExpenseChart(canvas, type, labels, expense) {
        if (!canvas) return;
        this.createChart(canvas, {
            type: type,
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Expense',
                        data: expense,
                        type: type === 'bar' ? 'polarArea' : 'bar',
                    },
                ]
            },
        });
    }

    renderProfitChart(canvas, type, labels, profit) {
        if (!canvas) return;
        this.createChart(canvas, {
            type: type,
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Profit/Loss',
                        data: profit,
                        fill: true,
                        borderColor: 'rgba(245, 65, 10, 1)',
                    },
                ]
            },
        });
    }

    renderAllInOneChart(canvas, type, labels, data, expense, profit) {
        if (!canvas) return;
        this.createChart(canvas, {
            type: type,
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Income',
                        data: data,
                        type: type === 'line' ? 'line' : 'bar',
                        backgroundColor: 'rgba(39, 232, 232, 0.5)',
                        borderColor: 'rgba(39, 232, 232, 1)',
                    },
                    {
                        label: 'Expense',
                        data: expense,
                        type: type === 'bar' ? 'radar' : 'bar',
                        backgroundColor: 'rgba(0, 0, 0, 0.5)',
                        borderColor: 'rgba(0, 0, 0, 1)',
                    },
                    {
                        label: 'Profit/Loss',
                        data: profit,
                        type: 'line',
                        fill: false,
                        borderColor: 'rgba(245, 65, 10, 1)',
                    },
                ]
            },
        });
    }
}
AccountDashboard.template = "AccountDashboard";
registry.category("actions").add('accounting_dashboard_tags', AccountDashboard);
