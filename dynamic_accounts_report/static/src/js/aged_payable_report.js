/** @odoo-module */
import { Component, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");
const today = luxon.DateTime.now();

export class AgedPayable extends Component {
    static template = 'age_p_template_new';

    tbody = signal.ref();
    date_range = signal.ref();
    date_to = signal.ref();
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
            total: null,
            currency: null,
            total_credit: null,
            diff0_sum: null,
            diff1_sum: null,
            diff2_sum: null,
            diff3_sum: null,
            diff4_sum: null,
            diff5_sum: null,
            selected_partner: [],
            selected_partner_rec: [],
        });
        this.load_data(this.initial_render = true);
    }

    async load_data() {
        let move_line_list = [];
        let move_lines_total = '';
        let diff0Sum = 0;
        let diff1Sum = 0;
        let diff2Sum = 0;
        let diff3Sum = 0;
        let diff4Sum = 0;
        let diff5Sum = 0;
        let TotalCredit = 0;
        let currency;
        var action_title = this.props?.action?.display_name || "Aged Payable";
        try {
            this.state.data = await this.orm.call("age.payable.report", "view_report", []);
            if (this.state.data) {
                for (const index in this.state.data) {
                    const value = this.state.data[index];
                    if (index !== 'partner_totals') {
                        move_line_list.push(index);
                    } else {
                        move_lines_total = value;
                        for (const moveLine of Object.values(move_lines_total)) {
                            currency = moveLine.currency_id;
                            diff0Sum += moveLine.diff0_sum || 0;
                            diff1Sum += moveLine.diff1_sum || 0;
                            diff2Sum += moveLine.diff2_sum || 0;
                            diff3Sum += moveLine.diff3_sum || 0;
                            diff4Sum += moveLine.diff4_sum || 0;
                            diff5Sum += moveLine.diff5_sum || 0;
                            TotalCredit += moveLine.credit_sum || 0;
                        }
                    }
                }
            }
            this.state.move_line = move_line_list;
            this.state.total = move_lines_total;
            this.state.currency = currency;
            this.state.total_credit = TotalCredit;
            this.state.diff0_sum = diff0Sum;
            this.state.diff1_sum = diff1Sum;
            this.state.diff2_sum = diff2Sum;
            this.state.diff3_sum = diff3Sum;
            this.state.diff4_sum = diff4Sum;
            this.state.diff5_sum = diff5Sum;
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

    gotoJournalItem(ev) {
        const idVal = ev.target.getAttribute("data-id") || ev.target.dataset.id;
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'account.move.line',
            name: "Journal Items",
            views: [[false, "list"]],
            domain: [["partner_id", "=", parseInt(idVal, 10)], ['account_type', 'in', ['liability_payable']]],
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

    async printPdf(ev) {
        if (ev && ev.preventDefault) {
            ev.preventDefault();
        }
        var action_title = this.props?.action?.display_name || "Aged Payable";
        let totals = {
            'diff0_sum': this.state.diff0_sum,
            'diff1_sum': this.state.diff1_sum,
            'diff2_sum': this.state.diff2_sum,
            'diff3_sum': this.state.diff3_sum,
            'diff4_sum': this.state.diff4_sum,
            'diff5_sum': this.state.diff5_sum,
            'total_credit': this.state.total_credit,
            'currency': this.state.currency,
        };
        return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'dynamic_accounts_report.aged_payable',
            'report_file': 'dynamic_accounts_report.aged_payable',
            'data': {
                'move_lines': this.state.move_line,
                'data': this.state.data,
                'total': this.state.total,
                'filters': this.filter(),
                'grand_total': totals,
                'title': action_title,
                'report_name': action_title
            },
            'display_name': action_title,
        });
    }

    filter() {
        const dateToEl = this.date_to() || this.date_range();
        let filters = {
            'partner': this.state.selected_partner_rec,
            'end_date': dateToEl?.value || null,
        };
        return filters;
    }

    async print_xlsx() {
        var action_title = this.props?.action?.display_name || "Aged Payable";
        let totals = {
            'diff0_sum': this.state.diff0_sum,
            'diff1_sum': this.state.diff1_sum,
            'diff2_sum': this.state.diff2_sum,
            'diff3_sum': this.state.diff3_sum,
            'diff4_sum': this.state.diff4_sum,
            'diff5_sum': this.state.diff5_sum,
            'total_credit': this.state.total_credit,
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
                'model': 'age.payable.report',
                'data': JSON.stringify(datas),
                'output_format': 'xlsx',
                'report_action': this.props?.action?.xml_id || 'dynamic_accounts_report.action_aged_payable',
                'report_name': action_title,
            },
        };
        await download({
            url: '/dynamic_account/xlsx_report',
            data: action.data,
            error: (error) => console.error(error),
        });
    }

    async applyFilter(ev, e, is_delete = false) {
        let move_line_list = [];
        let move_lines_total = '';
        let diff0Sum = 0;
        let diff1Sum = 0;
        let diff2Sum = 0;
        let diff3Sum = 0;
        let diff4Sum = 0;
        let diff5Sum = 0;
        let TotalCredit = 0;
        const dateToEl = this.date_to() || this.date_range();
        if (ev && ev.target && ev.target.attributes && ev.target.attributes["data-value"]) {
            const dataVal = ev.target.attributes["data-value"].value;
            if (dateToEl) {
                if (dataVal == 'today') {
                    dateToEl.value = today.toFormat('yyyy-MM-dd');
                } else if (dataVal == 'last-month-end') {
                    dateToEl.value = today.startOf('month').minus({ days: 1 }).toFormat('yyyy-MM-dd');
                } else if (dataVal == 'last-quarter-end') {
                    dateToEl.value = today.startOf('quarter').minus({ days: 1 }).toFormat('yyyy-MM-dd');
                } else if (dataVal == 'last-year-end') {
                    dateToEl.value = today.startOf('year').minus({ days: 1 }).toFormat('yyyy-MM-dd');
                }
            }
        } else if (e && e.input && e.input.attributes?.placeholder?.value == 'Partner' && !is_delete) {
            this.state.selected_partner.push(ev[0].id);
            this.state.selected_partner_rec.push(ev[0]);
        } else if (is_delete) {
            let index = this.state.selected_partner_rec.indexOf(ev);
            this.state.selected_partner_rec.splice(index, 1);
            this.state.selected_partner = this.state.selected_partner_rec.map((rec) => rec.id);
        }
        const endDateVal = dateToEl?.value || null;
        let filtered_data = await this.orm.call("age.payable.report", "get_filter_values", [endDateVal, this.state.selected_partner]);
        for (const index in filtered_data) {
            const value = filtered_data[index];
            if (index !== 'partner_totals') {
                move_line_list.push(index);
            } else {
                move_lines_total = value;
                for (const moveLine of Object.values(move_lines_total)) {
                    diff0Sum += moveLine.diff0_sum || 0;
                    diff1Sum += moveLine.diff1_sum || 0;
                    diff2Sum += moveLine.diff2_sum || 0;
                    diff3Sum += moveLine.diff3_sum || 0;
                    diff4Sum += moveLine.diff4_sum || 0;
                    diff5Sum += moveLine.diff5_sum || 0;
                    TotalCredit += moveLine.credit_sum || 0;
                }
            }
        }
        this.state.data = filtered_data;
        this.state.move_line = move_line_list;
        this.state.total = move_lines_total;
        this.state.total_credit = TotalCredit;
        this.state.diff0_sum = diff0Sum;
        this.state.diff1_sum = diff1Sum;
        this.state.diff2_sum = diff2Sum;
        this.state.diff3_sum = diff3Sum;
        this.state.diff4_sum = diff4Sum;
        this.state.diff5_sum = diff5Sum;
    }

    getDomain() {
        return [];
    }
}

actionRegistry.add("age_p", AgedPayable);
