import {Component, signal, proxy} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {download} from "@web/core/network/download";

const actionRegistry = registry.category("actions");

export class CashBook extends Component {
    static template = 'csh_b_template_new';

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
            move_line: null,
            data: null,
            total: null,
            accounts: null,
            filter_applied: null,
            selected_partner: [],
            selected_partner_rec: [],
            date_range: null,
            date_range_title: null,
            options: null,
            selected_account_list: [],
            total_debit: null,
            total_debit_display: null,
            total_credit: null,
            total_credit_display: null,
            currency: null,
            message_list: [],
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
        let move_line_list = [];
        let move_lines_total = {};
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency = this.state.currency || '';

        if (data) {
            if (data.currency) {
                currency = data.currency;
            }
            if (data.accounts) {
                this.state.accounts = data.accounts;
            }
            for (const index in data) {
                const value = data[index];
                if (index !== 'move_lines_total' && index !== 'accounts' && index !== 'currency') {
                    move_line_list.push(index);
                } else if (index === 'move_lines_total') {
                    move_lines_total = value || {};
                    for (const moveLine of Object.values(move_lines_total)) {
                        if (moveLine.currency_id) {
                            currency = moveLine.currency_id;
                        }
                        totalDebitSum += moveLine.total_debit || 0;
                        totalCreditSum += moveLine.total_credit || 0;
                        moveLine.total_debit_display = this.formatNumberWithSeparators(moveLine.total_debit || 0);
                        moveLine.total_credit_display = this.formatNumberWithSeparators(moveLine.total_credit || 0);
                        moveLine.balance = this.formatNumberWithSeparators((moveLine.total_debit || 0) - (moveLine.total_credit || 0));
                    }
                }
            }
            if (move_line_list) {
                for (const key of move_line_list) {
                    if (Array.isArray(data[key])) {
                        for (const line of data[key]) {
                            if (line.debit !== undefined) {
                                line.debit_display = this.formatNumberWithSeparators(line.debit || 0);
                            }
                            if (line.credit !== undefined) {
                                line.credit_display = this.formatNumberWithSeparators(line.credit || 0);
                            }
                            if (line.balance !== undefined) {
                                line.balance_display = this.formatNumberWithSeparators(line.balance || 0);
                            }
                        }
                    }
                }
            }
        }
        this.state.move_line = move_line_list;
        this.state.data = data;
        this.state.total = move_lines_total;
        this.state.currency = currency;
        this.state.total_debit = Math.round(totalDebitSum * 100) / 100;
        this.state.total_debit_display = this.formatNumberWithSeparators(totalDebitSum);
        this.state.total_credit = Math.round(totalCreditSum * 100) / 100;
        this.state.total_credit_display = this.formatNumberWithSeparators(totalCreditSum);
    }

    async load_data() {
        try {
            const data = await this.orm.call("cash.book.report", "view_report", []);
            this._processData(data);
        } catch (el) {
            console.error(el);
        }
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

    async printPdf(ev) {
        if (ev && ev.preventDefault) {
            ev.preventDefault();
        }
        var action_title = this.props?.action?.display_name || "Cash Book";
        let totals = {
            'total_debit': this.state.total_debit,
            'total_debit_display': this.state.total_debit_display,
            'total_credit': this.state.total_credit,
            'total_credit_display': this.state.total_credit_display,
            'currency': this.state.currency || false,
        };
        return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'dynamic_accounts_report.bank_book',
            'report_file': 'dynamic_accounts_report.bank_book',
            'data': {
                'move_lines': this.state.move_line,
                'filters': this.filter(),
                'grand_total': totals,
                'data': this.state.data,
                'total': this.state.total,
                'title': action_title,
                'report_name': action_title
            },
            'display_name': action_title,
        });
    }

    filter() {
        const accountNames = (this.state.selected_account_list || []).map(id => {
            const acc = (this.state.accounts || []).find(item => item.id === id);
            return acc ? (acc.name || acc.display_name) : id;
        });
        let filters = {
            'partner': this.state.selected_partner_rec,
            'account': accountNames,
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

    async print_xlsx() {
        var action_title = this.props?.action?.display_name || "Cash Book";
        let totals = {
            'total_debit': this.state.total_debit,
            'total_debit_display': this.state.total_debit_display,
            'total_credit': this.state.total_credit,
            'total_credit_display': this.state.total_credit_display,
            'currency': this.state.currency || false,
        };
        var datas = {
            'move_lines': this.state.move_line,
            'data': this.state.data,
            'total': this.state.total,
            'filters': this.filter(),
            'grand_total': totals,
            'title': action_title,
        };
        var action = {
            'data': {
                'model': 'cash.book.report',
                'data': JSON.stringify(datas),
                'output_format': 'xlsx',
                'report_action': this.props?.action?.xml_id || 'dynamic_accounts_report.action_cash_book',
                'report_name': action_title,
            },
        };
        await download({
            url: '/dynamic_account/xlsx_report',
            data: action.data,
            error: (error) => console.error(error),
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
            } else if (dataVal === 'account') {
                const accountId = parseInt(target.getAttribute("data-id"), 10);
                if (!this.state.selected_account_list.includes(accountId)) {
                    this.state.selected_account_list = [...this.state.selected_account_list, accountId];
                } else {
                    this.state.selected_account_list = this.state.selected_account_list.filter(id => id !== accountId);
                }
            } else if (dataVal === 'draft') {
                if (this.state.options && this.state.options.draft) {
                    const {draft, ...updatedAccount} = this.state.options;
                    this.state.options = Object.keys(updatedAccount).length ? updatedAccount : null;
                } else {
                    this.state.options = {
                        ...(this.state.options || {}),
                        'draft': true
                    };
                }
            }
        }
        let filtered_data = await this.orm.call(
            "cash.book.report",
            "get_filter_values",
            [
                this.state.selected_partner,
                this.state.date_range,
                this.state.selected_account_list,
                this.state.options
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
actionRegistry.add("csh_b", CashBook);
