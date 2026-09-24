/** @odoo-module */
import { Component, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");

export class GeneralLedger extends Component {
    static template = 'gl_template_new';

    tbody = signal.ref();
    unfoldButton = signal.ref();
    date_from = signal.ref();
    date_to = signal.ref();
    table_view_gl = signal.ref();

    setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.dialog = useService("dialog");
        this.state = proxy({
            account: null,
            account_data: null,
            account_data_list: null,
            account_total: null,
            total_debit: null,
            total_debit_display: null,
            total_credit_display: null,
            total_credit: null,
            currency: null,
            journals: null,
            selected_journal_list: [],
            analytics: null,
            selected_analytic_list: [],
            title: null,
            filter_applied: null,
            account_list: null,
            account_total_list: null,
            date_range: null,
            options: null,
            method: {
                'accural': true
            },
        });
        this.load_data(this.initial_render = true);
    }

    formatNumberWithSeparators(number) {
        const parsedNumber = parseFloat(number);
        if (isNaN(parsedNumber)) {
            return "0.00";
        }
        return parsedNumber.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    async load_data() {
        let account_list = [];
        let account_totals = '';
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency;
        var action_title = this.props?.action?.display_name || "General Ledger";
        try {
            this.state.account_data = await this.orm.call("account.general.ledger", "view_report", [[this.wizard_id], action_title]);
            const dataArray = this.state.account_data;
            if (dataArray) {
                Object.entries(dataArray).forEach(([key, value]) => {
                    if (key !== 'account_totals' && key !== 'journal_ids' && key !== 'analytic_ids') {
                        account_list.push(key);
                        if (Array.isArray(value)) {
                            value.forEach(entry => {
                                if (entry && entry[0]) {
                                    entry[0].debit_display = this.formatNumberWithSeparators(entry[0].debit || 0);
                                    entry[0].credit_display = this.formatNumberWithSeparators(entry[0].credit || 0);
                                }
                            });
                        }
                    } else if (key === 'journal_ids') {
                        this.state.journals = value;
                    } else if (key === 'analytic_ids') {
                        this.state.analytics = value;
                    } else {
                        account_totals = value;
                    }
                });
            }
            if (account_totals) {
                Object.values(account_totals).forEach(account => {
                    currency = account.currency_id;
                    totalDebitSum += account.total_debit || 0;
                    totalCreditSum += account.total_credit || 0;
                    account.total_debit_display = this.formatNumberWithSeparators(account.total_debit || 0);
                    account.total_credit_display = this.formatNumberWithSeparators(account.total_credit || 0);
                    account.balance_display = this.formatNumberWithSeparators(account.total_debit - account.total_credit || 0);
                });
            }
            this.state.account = account_list;
            this.state.account_list = account_list;
            this.state.account_total_list = account_totals;
            this.state.account_total = account_totals;
            this.state.currency = currency;
            this.state.total_debit = totalDebitSum;
            this.state.total_debit_display = this.formatNumberWithSeparators(totalDebitSum);
            this.state.total_credit = totalCreditSum;
            this.state.total_credit_display = this.formatNumberWithSeparators(totalCreditSum);
            this.state.title = action_title;
        } catch (el) {
            console.error(el);
        }
    }

    async printPdf(ev) {
        if (ev && ev.preventDefault) {
            ev.preventDefault();
        }
        let totals = {
            'total_debit': this.state.total_debit,
            'total_debit_display': this.state.total_debit_display,
            'total_credit': this.state.total_credit,
            'total_credit_display': this.state.total_credit_display,
            'currency': this.state.currency,
        };
        var action_title = this.props?.action?.display_name || "General Ledger";
        return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'dynamic_accounts_report.general_ledger',
            'report_file': 'dynamic_accounts_report.general_ledger',
            'data': {
                'account': this.state.account,
                'filters': this.filter(),
                'grand_total': totals,
                'account_data': this.state.account_data,
                'total': this.state.account_total,
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
            const today = new Date();
            if (this.state.date_range === 'year') {
                startDate = new Date(today.getFullYear(), 0, 1);
                endDate = new Date(today.getFullYear(), 11, 31);
            } else if (this.state.date_range === 'quarter') {
                const currentQuarter = Math.floor(today.getMonth() / 3);
                startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
                endDate = new Date(today.getFullYear(), (currentQuarter + 1) * 3, 0);
            } else if (this.state.date_range === 'month') {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            } else if (this.state.date_range === 'last-month') {
                startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                endDate = new Date(today.getFullYear(), today.getMonth(), 0);
            } else if (this.state.date_range === 'last-year') {
                startDate = new Date(today.getFullYear() - 1, 0, 1);
                endDate = new Date(today.getFullYear() - 1, 11, 31);
            } else if (this.state.date_range === 'last-quarter') {
                const lastQuarter = Math.floor((today.getMonth() - 3) / 3);
                startDate = new Date(today.getFullYear(), lastQuarter * 3, 1);
                endDate = new Date(today.getFullYear(), (lastQuarter + 1) * 3, 0);
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
            'journal': this.state.selected_journal_list,
            'analytic': this.state.selected_analytic_list,
            'options': this.state.options,
            'start_date': null,
            'end_date': null,
        };
        if (startYear !== undefined && startMonth !== undefined && startDay !== undefined &&
            endYear !== undefined && endMonth !== undefined && endDay !== undefined) {
            filters['start_date'] = `${startYear}-${startMonth < 10 ? '0' : ''}${startMonth}-${startDay < 10 ? '0' : ''}${startDay}`;
            filters['end_date'] = `${endYear}-${endMonth < 10 ? '0' : ''}${endMonth}-${endDay < 10 ? '0' : ''}${endDay}`;
        }
        return filters;
    }

    async print_xlsx() {
        var action_title = this.props?.action?.display_name || "General Ledger";
        let totals = {
            'total_debit': this.state.total_debit,
            'total_debit_display': this.state.total_debit_display,
            'total_credit': this.state.total_credit,
            'total_credit_display': this.state.total_credit_display,
            'currency': this.state.currency,
        };
        var datas = {
            'account': this.state.account,
            'account_data': this.state.account_data,
            'total': this.state.account_total,
            'title': action_title,
            'filters': this.filter(),
            'grand_total': totals,
        };
        var action = {
            'data': {
                'model': 'account.general.ledger',
                'data': JSON.stringify(datas),
                'output_format': 'xlsx',
                'report_action': this.props?.action?.xml_id || 'dynamic_accounts_report.action_general_ledger',
                'report_name': action_title,
            },
        };
        await download({
            url: '/dynamic_account/xlsx_report',
            data: action.data,
            error: (error) => console.error(error),
        });
    }

    gotoJournalEntry(ev) {
        const idVal = ev.target.getAttribute("data-id") || ev.target.dataset.id;
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'account.move',
            res_id: parseInt(idVal, 10),
            views: [[false, "form"]],
            target: "current",
        });
    }
    gotoJournalItem(ev) {
        const accountId = ev.target.getAttribute("data-id") || ev.target.dataset.id;
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Journal Items",
            res_model: 'account.move.line',
            views: [[false, "list"], [false, "form"]],
            domain: [['account_id', '=', parseInt(accountId, 10)]],
            target: "current",
        });
    }

    async unfoldAll(ev) {
        const tbodyEl = this.tbody();
        if (!tbodyEl) return;
        if (!ev.target.classList.contains("selected-filter")) {
            for (var length = 0; length < tbodyEl.children.length; length++) {
                tbodyEl.children[length].classList.add('show');
            }
            ev.target.classList.add("selected-filter");
        } else {
            for (var length = 0; length < tbodyEl.children.length; length++) {
                tbodyEl.children[length].classList.remove('show');
            }
            ev.target.classList.remove("selected-filter");
        }
    }

    async applyFilter(val, ev, is_delete = false) {
        let account_list = [];
        let account_totals = '';
        this.state.account = null;
        this.state.account_data = null;
        this.state.account_total = null;
        this.state.filter_applied = true;
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        if (ev) {
            if (ev.input && ev.input.attributes?.placeholder?.value == 'Journals' && !is_delete) {
                this.state.selected_journal_list.push(val[0].display_name);
            } else if (ev.input && ev.input.attributes?.placeholder?.value == 'Analytic' && !is_delete) {
                this.state.selected_analytic_list.push(val[0].display_name);
            } else if (is_delete && is_delete == 'journal') {
                let index = this.state.selected_journal_list.indexOf(val);
                this.state.selected_journal_list.splice(index, 1);
            } else if (is_delete && is_delete == 'analytic') {
                let index = this.state.selected_analytic_list.indexOf(val);
                this.state.selected_analytic_list.splice(index, 1);
            }
        } else if (val && val.target) {
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
            }
        }
        let filtered_data = await this.orm.call("account.general.ledger", "get_filter_values", [this.state.selected_journal_list, this.state.date_range, this.state.options, this.state.selected_analytic_list]);
        for (let index in filtered_data) {
            const value = filtered_data[index];
            if (index !== 'account_totals' && index !== 'journal_ids' && index !== 'analytic_ids') {
                account_list.push(index);
            } else if (index === 'account_totals') {
                account_totals = value;
                Object.values(account_totals).forEach(account_list => {
                    totalDebitSum += account_list.total_debit || 0;
                    totalCreditSum += account_list.total_credit || 0;
                });
}
        }
        this.state.account = account_list;
        this.state.account_data = filtered_data;
        this.state.account_total = account_totals;
        this.state.total_debit = totalDebitSum;
        this.state.total_credit = totalCreditSum;
        const unfoldBtn = this.unfoldButton();
        if (unfoldBtn && unfoldBtn.classList.contains("selected-filter")) {
            unfoldBtn.classList.remove("selected-filter");
        }
    }

    getDomain() {
        return [];
    }
}

actionRegistry.add("gen_l", GeneralLedger);
actionRegistry.add("g_l", GeneralLedger);
