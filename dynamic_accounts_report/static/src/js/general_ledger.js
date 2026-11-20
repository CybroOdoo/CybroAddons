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
            date_range_title: null,
            options: null,
            method: {
                'accrual': true
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

    _processData(data) {
        let account_list = [];
        let account_totals = {};
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency = this.state.currency || '';

        if (data) {
            Object.entries(data).forEach(([key, value]) => {
                if (key !== 'account_totals' && key !== 'journal_ids' && key !== 'analytic_ids' && key !== 'currency') {
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
                } else if (key === 'currency') {
                    currency = value;
                } else if (key === 'account_totals') {
                    account_totals = value || {};
                }
            });
        }
        if (account_totals) {
            Object.values(account_totals).forEach(account => {
                if (account.currency_id) {
                    currency = account.currency_id;
                }
                totalDebitSum += account.total_debit || 0;
                totalCreditSum += account.total_credit || 0;
                account.total_debit_display = this.formatNumberWithSeparators(account.total_debit || 0);
                account.total_credit_display = this.formatNumberWithSeparators(account.total_credit || 0);
                account.balance_display = this.formatNumberWithSeparators((account.total_debit || 0) - (account.total_credit || 0));
            });
        }
        this.state.account = account_list;
        this.state.account_list = account_list;
        this.state.account_data = data;
        this.state.account_total = account_totals;
        this.state.account_total_list = account_totals;
        this.state.currency = currency;
        this.state.total_debit = Math.round(totalDebitSum * 100) / 100;
        this.state.total_debit_display = this.formatNumberWithSeparators(totalDebitSum);
        this.state.total_credit = Math.round(totalCreditSum * 100) / 100;
        this.state.total_credit_display = this.formatNumberWithSeparators(totalCreditSum);
    }

    async load_data() {
        var action_title = this.props?.action?.display_name || "General Ledger";
        try {
            const data = await this.orm.call("account.general.ledger", "view_report", [[this.wizard_id], action_title]);
            this._processData(data);
            this.state.title = action_title;
        } catch (el) {
            console.error(el);
        }
    }

    filter() {
        const journalNames = (this.state.selected_journal_list || []).map(id => {
            const j = (this.state.journals || []).find(item => item.id === id);
            return j ? j.name : id;
        });
        const analyticNames = (this.state.selected_analytic_list || []).map(id => {
            const a = (this.state.analytics || []).find(item => item.id === id);
            return a ? a.name : id;
        });
        let filters = {
            'journal': journalNames,
            'analytic': analyticNames,
            'options': this.state.options,
            'start_date': null,
            'end_date': null,
        };
        if (this.state.date_range) {
            if (typeof this.state.date_range === 'object' && this.state.date_range !== null) {
                filters['start_date'] = this.state.date_range.start_date || null;
                filters['end_date'] = this.state.date_range.end_date || null;
                return filters;
            }
            let startDate, endDate;
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
            if (startDate && endDate) {
                const sY = startDate.getFullYear();
                const sM = String(startDate.getMonth() + 1).padStart(2, '0');
                const sD = String(startDate.getDate()).padStart(2, '0');
                const eY = endDate.getFullYear();
                const eM = String(endDate.getMonth() + 1).padStart(2, '0');
                const eD = String(endDate.getDate()).padStart(2, '0');
                filters['start_date'] = `${sY}-${sM}-${sD}`;
                filters['end_date'] = `${eY}-${eM}-${eD}`;
            }
        }
        return filters;
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
        this.state.filter_applied = true;
        const target = val && val.target ? (val.target.closest("button, input") || val.target) : null;
        if (target) {
            const dataVal = target.getAttribute("data-value");
            if (target.name === 'start_date' || target.name === 'end_date') {
                const currentDates = (typeof this.state.date_range === 'object' && this.state.date_range !== null)
                    ? { ...this.state.date_range }
                    : {};
                if (target.value) {
                    currentDates[target.name] = target.value;
                } else {
                    delete currentDates[target.name];
                }
                if (Object.keys(currentDates).length > 0) {
                    this.state.date_range = currentDates;
                    const s = currentDates.start_date || '';
                    const e = currentDates.end_date || '';
                    this.state.date_range_title = (s && e) ? `${s} to ${e}` : (s ? `From ${s}` : `To ${e}`);
                } else {
                    this.state.date_range = null;
                    this.state.date_range_title = null;
                }
            } else if (['month', 'year', 'quarter', 'last-month', 'last-year', 'last-quarter'].includes(dataVal)) {
                if (this.state.date_range === dataVal) {
                    this.state.date_range = null;
                    this.state.date_range_title = null;
                } else {
                    this.state.date_range = dataVal;
                    this.state.date_range_title = target.innerText.trim();
                    const startInput = document.getElementById("start_date");
                    const endInput = document.getElementById("end_date");
                    if (startInput) startInput.value = "";
                    if (endInput) endInput.value = "";
                }
            } else if (dataVal === 'journal') {
                const journalId = parseInt(target.getAttribute("data-id"), 10);
                if (!this.state.selected_journal_list.includes(journalId)) {
                    this.state.selected_journal_list = [...this.state.selected_journal_list, journalId];
                } else {
                    this.state.selected_journal_list = this.state.selected_journal_list.filter(id => id !== journalId);
                }
            } else if (dataVal === 'analytic') {
                const analyticId = parseInt(target.getAttribute("data-id"), 10);
                if (!this.state.selected_analytic_list.includes(analyticId)) {
                    this.state.selected_analytic_list = [...this.state.selected_analytic_list, analyticId];
                } else {
                    this.state.selected_analytic_list = this.state.selected_analytic_list.filter(id => id !== analyticId);
                }
            } else if (dataVal === 'draft') {
                if (this.state.options && this.state.options.draft) {
                    const { draft, ...updatedOptions } = this.state.options;
                    this.state.options = Object.keys(updatedOptions).length ? updatedOptions : null;
                } else {
                    this.state.options = {
                        ...(this.state.options || {}),
                        'draft': true
                    };
                }
            } else if (dataVal === 'cash-basis') {
                if (this.state.method && this.state.method.cash) {
                    const { cash, ...updatedMethod } = this.state.method;
                    this.state.method = Object.keys(updatedMethod).length ? updatedMethod : { 'accrual': true };
                } else {
                    this.state.method = {
                        ...(this.state.method || {}),
                        'cash': true
                    };
                }
            }
        }
        let filtered_data = await this.orm.call(
            "account.general.ledger",
            "get_filter_values",
            [
                this.state.selected_journal_list,
                this.state.date_range,
                this.state.options,
                this.state.selected_analytic_list,
                this.state.method
            ]
        );
        this._processData(filtered_data);
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
