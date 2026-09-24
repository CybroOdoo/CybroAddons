/** @odoo-module */
import { Component, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");
const today = luxon.DateTime.now();
let monthNamesShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export class TaxReport extends Component {
    static template = 'tax_r_template_new';

    tbody = signal.ref();
    end_date = signal.ref();
    start_date = signal.ref();
    date_from = signal.ref();
    date_to = signal.ref();
    periods = signal.ref();
    global = signal.ref();
    account = signal.ref();
    tax = signal.ref();
    period = signal.ref();
    period_year = signal.ref();
    unfoldButton = signal.ref();
    table_view_gl = signal.ref();

    async setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.state = proxy({
            move_line: null,
            data: null,
            sale_total: 0.0,
            purchase_total: 0.0,
            total: null,
            journals: null,
            selected_analytic: [],
            analytic_account: null,
            selected_journal_list: [],
            selected_analytic_account_rec: [],
            date_range: 'month',
            date_type: 'month',
            apply_comparison: false,
            comparison_type: null,
            date_viewed: [],
            comparison_number: null,
            options: null,
            report_type: null,
            method: {
                'accural': true
            },
        });
        this.load_data(this.initial_render = true);
    }

    async load_data() {
        let move_line_list = [];
        let move_lines_total = '';
        var action_title = this.props?.action?.display_name || "Tax Report";
        try {
            var todayDate = new Date();
            var startOfMonth = new Date(todayDate.getFullYear(), todayDate.getMonth(), 1);
            var endOfMonth = new Date(todayDate.getFullYear(), todayDate.getMonth() + 1, 0);
            var formattedStartDate = startOfMonth.getFullYear() + '-' +
                (('0' + (startOfMonth.getMonth() + 1)).slice(-2)) + '-' +
                (('0' + startOfMonth.getDate()).slice(-2));
            var formattedEndDate = endOfMonth.getFullYear() + '-' +
                (('0' + (endOfMonth.getMonth() + 1)).slice(-2)) + '-' +
                (('0' + endOfMonth.getDate()).slice(-2));
            var start_month = monthNamesShort[startOfMonth.getMonth()];

            this.state.data = await this.orm.call("tax.report", "view_report", []);
            if (this.state.data) {
                this.state.sale_total = this.state.data.sale_total;
                this.state.purchase_total = this.state.data.purchase_total;
            }
            if (this.state.date_viewed.length === 0) {
                this.state.date_viewed.push(start_month + " " + startOfMonth.getFullYear());
            }
        } catch (el) {
            console.error(el);
        }
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }

    async printPdf(ev) {
        if (ev && ev.preventDefault) {
            ev.preventDefault();
        }
        var action_title = this.props?.action?.display_name || "Tax Report";
        let comparison_number_range = this.comparison_number_range;
        let data_viewed = this.state.date_viewed;
        if (this.state.apply_comparison) {
            if (this.comparison_number_range.length > 10) {
                comparison_number_range = this.comparison_number_range.slice(-10);
                data_viewed = this.state.date_viewed.slice(-11);
            }
        }
        return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'dynamic_accounts_report.tax_report',
            'report_file': 'dynamic_accounts_report.tax_report',
            'data': {
                'data': this.state.data,
                'sale_total': this.state.sale_total,
                'purchase_total': this.state.purchase_total,
                'date_viewed': data_viewed,
                'filters': this.filter(),
                'apply_comparison': this.state.apply_comparison,
                'comparison_number_range': comparison_number_range,
                'report_type': this.state.report_type,
                'title': action_title,
                'report_name': action_title
            },
            'display_name': action_title,
        });
    }

    filter() {
        let startDate, endDate;
        let startYear, startMonth, startDay, endYear, endMonth, endDay;
        if (this.state.date_range) {
            const todayDate = new Date();
            if (this.state.date_range === 'year') {
                startDate = new Date(todayDate.getFullYear(), 0, 1);
                endDate = new Date(todayDate.getFullYear(), 11, 31);
            } else if (this.state.date_range === 'quarter') {
                const currentQuarter = Math.floor(todayDate.getMonth() / 3);
                startDate = new Date(todayDate.getFullYear(), currentQuarter * 3, 1);
                endDate = new Date(todayDate.getFullYear(), (currentQuarter + 1) * 3, 0);
            } else if (this.state.date_range === 'month') {
                startDate = new Date(todayDate.getFullYear(), todayDate.getMonth(), 1);
                endDate = new Date(todayDate.getFullYear(), todayDate.getMonth() + 1, 0);
            } else if (this.state.date_range === 'last-month') {
                startDate = new Date(todayDate.getFullYear(), todayDate.getMonth() - 1, 1);
                endDate = new Date(todayDate.getFullYear(), todayDate.getMonth(), 0);
            } else if (this.state.date_range === 'last-year') {
                startDate = new Date(todayDate.getFullYear() - 1, 0, 1);
                endDate = new Date(todayDate.getFullYear() - 1, 11, 31);
            } else if (this.state.date_range === 'last-quarter') {
                const lastQuarter = Math.floor((todayDate.getMonth() - 3) / 3);
                startDate = new Date(todayDate.getFullYear(), lastQuarter * 3, 1);
                endDate = new Date(todayDate.getFullYear(), (lastQuarter + 1) * 3, 0);
            }
            if (startDate) {
                startYear = startDate.getFullYear();
                startMonth = startDate.getMonth() + 1;
                startDay = startDate.getDate();
            }
            if (endDate) {
                endYear = endDate.getFullYear();
                endMonth = endDate.getMonth() + 1;
                endDay = endDate.getDate();
            }
        }
        let filters = {
            'options': this.state.options,
            'start_date': null,
            'end_date': null,
            'comparison_type': this.state.comparison_type,
            'comparison_number_range': this.state.comparison_number,
        };
        if (startYear !== undefined && startMonth !== undefined && startDay !== undefined &&
            endYear !== undefined && endMonth !== undefined && endDay !== undefined) {
            filters['start_date'] = `${startYear}-${startMonth < 10 ? '0' : ''}${startMonth}-${startDay < 10 ? '0' : ''}${startDay}`;
            filters['end_date'] = `${endYear}-${endMonth < 10 ? '0' : ''}${endMonth}-${endDay < 10 ? '0' : ''}${endDay}`;
        }
        return filters;
    }

    async print_xlsx() {
        var action_title = this.props?.action?.display_name || "Tax Report";
        let comparison_number_range = this.comparison_number_range;
        let data_viewed = this.state.date_viewed;
        if (this.state.apply_comparison) {
            if (this.comparison_number_range.length > 10) {
                comparison_number_range = this.comparison_number_range.slice(-10);
                data_viewed = this.state.date_viewed.slice(-11);
            }
        }
        var datas = {
            'data': this.state.data,
            'title': action_title,
            'filters': this.filter(),
            'sale_total': this.state.sale_total,
            'purchase_total': this.state.purchase_total,
            'date_viewed': data_viewed,
            'apply_comparison': this.state.apply_comparison,
            'comparison_number_range': comparison_number_range,
            'report_type': this.state.report_type,
        };
        var action = {
            'data': {
                'model': 'tax.report',
                'data': JSON.stringify(datas),
                'output_format': 'xlsx',
                'report_action': this.props?.action?.xml_id || 'dynamic_accounts_report.action_tax_report',
                'report_name': action_title,
            },
        };
        await download({
            url: '/dynamic_account/xlsx_report',
            data: action.data,
            error: (error) => console.error(error),
        });
    }

    async applyFilter(val, ev, is_delete = false) {
        this.state.data = null;
        this.state.filter_applied = true;

        if (val && val.target) {
            const dataVal = val.target.getAttribute("data-value");
            if (val.target.name === 'start_date') {
                this.state.date_range = {
                    ...this.state.date_range,
                    start_date: val.target.value
                };
            } else if (val.target.name === 'end_date') {
                this.state.date_range = {
                    ...this.state.date_range,
                    end_date: val.target.value
                };
            } else if (['month', 'year', 'quarter', 'last-month', 'last-year', 'last-quarter'].includes(dataVal)) {
                this.state.date_range = dataVal;
            } else if (dataVal === 'draft') {
                if (val.target.classList.contains("selected-filter")) {
                    const { draft, ...updatedAccount } = this.state.options || {};
                    this.state.options = updatedAccount;
                    val.target.classList.remove("selected-filter");
                } else {
                    this.state.options = {
                        ...(this.state.options || {}),
                        'draft': true
                    };
                    val.target.classList.add("selected-filter");
                }
            } else if (dataVal === 'tax') {
                this.state.report_type = { 'tax': true };
            } else if (dataVal === 'account') {
                this.state.report_type = { 'account': true };
            }
        }


        let computedDates = this.filter();
        let filtered_data = await this.orm.call("tax.report", "get_filter_values", [
            computedDates.start_date,
            computedDates.end_date,
            this.state.comparison_number,
            this.state.comparison_type,
            this.state.options,
            this.state.report_type
        ]);
        this.state.data = filtered_data;
        if (this.state.data) {
            this.state.sale_total = this.state.data.sale_total;
            this.state.purchase_total = this.state.data.purchase_total;
        }
    }

    applyComparisonPeriod(ev) {
        this.state.apply_comparison = true;
        this.state.comparison_type = 'month';
        const periodEl = this.period();
        if (periodEl) {
            this.state.comparison_number = periodEl.value;
        }
        this.applyFilter(null, ev);
    }

    applyComparisonYear(ev) {
        this.state.apply_comparison = true;
        this.state.comparison_type = 'year';
        this.applyFilter(null, ev);
    }

    async applyComparison(ev) {
        this.state.apply_comparison = false;
        this.state.comparison_type = null;
        this.state.comparison_number = null;
        const lastIndex = this.state.date_viewed.length - 1;
        this.state.date_viewed.splice(0, lastIndex);
        this.applyFilter(null, ev);
    }

    get comparison_number_range() {
        const range = [];
        if (this.state.comparison_number) {
            for (let i = 1; i <= this.state.comparison_number; i++) {
                range.push(i);
            }
        }
        return range.reverse();
    }
}

actionRegistry.add("tax_r", TaxReport);
