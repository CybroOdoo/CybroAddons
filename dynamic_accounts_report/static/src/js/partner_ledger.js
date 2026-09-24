/** @odoo-module */
import { Component, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");

export class PartnerLedger extends Component {
    static template = 'pl_template_new';

    tbody = signal.ref();
    unfoldButton = signal.ref();
    date_from = signal.ref();
    date_to = signal.ref();
    table_view_pl = signal.ref();

    setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.dialog = useService("dialog");
        this.state = proxy({
            partners: null,
            data: null,
            total: null,
            title: null,
            currency: null,
            filter_applied: null,
            selected_partner: [],
            selected_partner_rec: [],
            total_debit: null,
            total_debit_display: null,
            total_credit: null,
            partner_list: null,
            total_list: null,
            date_range: null,
            account: null,
            options: null,
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

    async load_data() {
        let partner_list = [];
        let partner_totals = '';
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency;
        var action_title = this.props?.action?.display_name || "Partner Ledger";
        try {
            this.state.data = await this.orm.call("account.partner.ledger", "view_report", [[this.wizard_id], action_title]);
            const dataArray = this.state.data;
            if (dataArray) {
                Object.entries(dataArray).forEach(([key, value]) => {
                    if (key !== 'partner_totals') {
                        partner_list.push(key);
                        if (Array.isArray(value)) {
                            value.forEach(entry => {
                                if (entry && entry[0]) {
                                    entry[0].debit_display = this.formatNumberWithSeparators(entry[0].debit || 0);
                                    entry[0].credit_display = this.formatNumberWithSeparators(entry[0].credit || 0);
                                    entry[0].amount_currency_display = this.formatNumberWithSeparators(entry[0].amount_currency || 0);
                                }
                            });
                        }
                    } else {
                        partner_totals = value;
                    }
                });
            }
            if (partner_totals) {
                Object.values(partner_totals).forEach(partner => {
                    currency = partner.currency_id;
                    totalDebitSum += partner.total_debit || 0;
                    totalCreditSum += partner.total_credit || 0;
                    partner.total_debit_display = this.formatNumberWithSeparators(partner.total_debit || 0);
                    partner.total_credit_display = this.formatNumberWithSeparators(partner.total_credit || 0);
                });
            }
            this.state.partners = partner_list;
            this.state.partner_list = partner_list;
            this.state.total_list = partner_totals;
            this.state.total = partner_totals;
            this.state.currency = currency;
            this.state.total_debit = totalDebitSum;
            this.state.total_debit_display = this.formatNumberWithSeparators(this.state.total_debit || 0);
            this.state.total_credit = totalCreditSum;
            this.state.total_credit_display = this.formatNumberWithSeparators(this.state.total_credit || 0);
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
        var action_title = this.props?.action?.display_name || "Partner Ledger";
        return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'dynamic_accounts_report.partner_ledger',
            'report_file': 'dynamic_accounts_report.partner_ledger',
            'data': {
                'partners': this.state.partners,
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
            'account': this.state.account,
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
        let totals = {
            'total_debit': this.state.total_debit,
            'total_credit': this.state.total_credit,
            'currency': this.state.currency,
        };
        var action_title = this.props?.action?.display_name || "Partner Ledger";
        var datas = {
            'partners': this.state.partners,
            'data': this.state.data,
            'total': this.state.total,
            'title': action_title,
            'filters': this.filter(),
            'grand_total': totals,
        };
        var action = {
            'data': {
                'model': 'account.partner.ledger',
                'data': JSON.stringify(datas),
                'output_format': 'xlsx',
                'report_action': this.props?.action?.xml_id || 'dynamic_accounts_report.action_partner_ledger',
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
        const idVal = ev.target.getAttribute("data-id") || ev.target.dataset.id;
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'account.move.line',
            name: "Journal Items",
            views: [[false, "list"]],
            domain: [["partner_id", "=", parseInt(idVal, 10)], ['account_type', 'in', ['liability_payable', 'asset_receivable']]],
            target: "current",
        });
    }

    openPartner(ev) {
        const idVal = ev.target.getAttribute("data-id") || ev.target.dataset.id;
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'res.partner',
            res_id: parseInt(idVal, 10),
            views: [[false, "form"]],
            target: "current",
        });
    }

    async applyFilter(val, ev, is_delete = false) {
        let partner_list = [];
        let partner_totals = '';
        this.state.partners = null;
        this.state.data = null;
        this.state.total = null;
        this.state.filter_applied = true;
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        if (ev) {
            if (ev.input && ev.input.attributes?.placeholder?.value == 'Partner' && !is_delete) {
                this.state.selected_partner.push(val[0].id);
                this.state.selected_partner_rec.push(val[0]);
            } else if (is_delete) {
                let index = this.state.selected_partner_rec.indexOf(val);
                this.state.selected_partner_rec.splice(index, 1);
                this.state.selected_partner = this.state.selected_partner_rec.map((rec) => rec.id);
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
            } else if (dataVal === 'receivable') {
                if (val.target.classList.contains("selected-filter")) {
                    const { Receivable, ...updatedAccount } = this.state.account || {};
                    this.state.account = updatedAccount;
                    val.target.classList.remove("selected-filter");
                } else {
                    this.state.account = {
                        ...(this.state.account || {}),
                        'Receivable': true
                    };
                    val.target.classList.add("selected-filter");
                }
            } else if (dataVal === 'payable') {
                if (val.target.classList.contains("selected-filter")) {
                    const { Payable, ...updatedAccount } = this.state.account || {};
                    this.state.account = updatedAccount;
                    val.target.classList.remove("selected-filter");
                } else {
                    this.state.account = {
                        ...(this.state.account || {}),
                        'Payable': true
                    };
                    val.target.classList.add("selected-filter");
                }
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
        let filtered_data = await this.orm.call("account.partner.ledger", "get_filter_values", [this.state.selected_partner, this.state.date_range, this.state.account, this.state.options]);
        for (let index in filtered_data) {
            const value = filtered_data[index];
            if (index !== 'partner_totals') {
                partner_list.push(index);
            } else {
                partner_totals = value;
                Object.values(partner_totals).forEach(partner_list => {
                    totalDebitSum += partner_list.total_debit || 0;
                    totalCreditSum += partner_list.total_credit || 0;
                });
            }
        }
        this.state.partners = partner_list;
        this.state.data = filtered_data;
        this.state.total = partner_totals;
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
}

actionRegistry.add("p_l", PartnerLedger);
