/** @odoo-module */
import { Component, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";
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
            selected_account_list: [],
            total_debit: null,
            total_credit: null,
            currency: null,
            options: null,
            message_list: [],
        });
        this.load_data(this.initial_render = true);
    }

    async load_data() {
        let move_line_list = [];
        let move_lines_total = '';
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency;
        var action_title = this.props?.action?.display_name || "Cash Book";
        try {
            this.state.data = await this.orm.call("cash.book.report", "view_report", []);
            if (this.state.data) {
                for (const index in this.state.data) {
                    const value = this.state.data[index];
                    if (index !== 'move_lines_total' && index !== 'accounts') {
                        move_line_list.push(index);
                    } else if (index === 'accounts') {
                        this.state.accounts = value;
                    } else {
                        move_lines_total = value;
                        for (const moveLine of Object.values(move_lines_total)) {
                            currency = moveLine.currency_id;
                            totalDebitSum += moveLine.total_debit || 0;
                            totalCreditSum += moveLine.total_credit || 0;
                        }
                    }
                }
            }
            this.state.move_line = move_line_list;
            this.state.total = move_lines_total;
            this.state.currency = currency;
            this.state.total_debit = totalDebitSum.toFixed(2);
            this.state.total_credit = totalCreditSum.toFixed(2);
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
            'total_credit': this.state.total_credit,
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
            'partner': this.state.selected_partner_rec,
            'account': this.state.selected_account_list,
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
        var action_title = this.props?.action?.display_name || "Cash Book";
        let totals = {
            'total_debit': this.state.total_debit,
            'total_credit': this.state.total_credit,
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
                'report_action': this.props?.action?.xml_id || 'dynamic_accounts_report.action_bank_book',
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
        let move_line_list = [];
        let move_lines_total = '';
        this.state.move_line = null;
        this.state.data = null;
        this.state.total = null;
        this.state.filter_applied = true;
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        if (ev) {
            if (ev.input && ev.input.attributes?.placeholder?.value == 'Partner' && !is_delete) {
                this.state.selected_partner.push(val[0].id);
                this.state.selected_partner_rec.push(val[0]);
            } else if (ev.input && ev.input.attributes?.placeholder?.value == 'Account' && !is_delete) {
                this.state.selected_account_list.push(val[0].display_name);
            } else if (is_delete && is_delete == 'partner') {
                let index = this.state.selected_partner_rec.indexOf(val);
                this.state.selected_partner_rec.splice(index, 1);
                this.state.selected_partner = this.state.selected_partner_rec.map((rec) => rec.id);
            } else if (is_delete && is_delete == 'account') {
                let index = this.state.selected_account_list.indexOf(val);
                this.state.selected_account_list.splice(index, 1);
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
        let filtered_data = await this.orm.call("cash.book.report", "get_filter_values", [this.state.selected_partner, this.state.date_range, this.state.options, this.state.selected_account_list]);
        for (let index in filtered_data) {
            const value = filtered_data[index];
            if (index !== 'move_lines_total' && index !== 'accounts') {
                move_line_list.push(index);
            } else {
                move_lines_total = value;
                for (const moveLine of Object.values(move_lines_total)) {
                    totalDebitSum += moveLine.total_debit || 0;
                    totalCreditSum += moveLine.total_credit || 0;
                }
            }
        }
        this.state.move_line = move_line_list;
        this.state.data = filtered_data;
        this.state.total = move_lines_total;
        this.state.total_debit = totalDebitSum.toFixed(2);
        this.state.total_credit = totalCreditSum.toFixed(2);
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
