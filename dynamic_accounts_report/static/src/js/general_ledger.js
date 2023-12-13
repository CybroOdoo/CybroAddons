/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");

class GeneralLedger extends owl.Component {
    setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.tbody = useRef('tbody');
        this.unfoldButton = useRef('unfoldButton');
        this.state = useState({
            account: null,
            account_data: null,
            account_data_list: null,
            account_total: null,
            total_debit: null,
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
        this.load_data(self.initial_render = true);
    }
    async load_data() {
        let account_list = []
        let account_totals = ''
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency;
        var self = this;
        var action_title = self.props.action.display_name;
        try {
            var self = this;
            self.state.account_data = await self.orm.call("account.general.ledger", "view_report", [[this.wizard_id], action_title,]);
            $.each(self.state.account_data, function (index, value) {
                if (index !== 'account_totals' && index !== 'journal_ids' && index !== 'analytic_ids') {
                    account_list.push(index)
                } else if (index == 'journal_ids') {
                    self.state.journals = value
                }
                else if (index == 'analytic_ids') {
                    self.state.analytics = value
                }
                else {
                    account_totals = value
                    Object.values(account_totals).forEach(account_list => {
                        currency = account_list.currency_id
                        totalDebitSum += account_list.total_debit || 0;
                        totalCreditSum += account_list.total_credit || 0;
                    });
                }
            })
            self.state.account = account_list
            self.state.account_list = account_list
            self.state.account_data_list = self.state.account_data
            self.state.account_total_list = account_totals
            self.state.account_total = account_totals
            self.state.currency = currency
            self.state.total_debit = totalDebitSum.toFixed(2)
            self.state.total_credit = totalCreditSum.toFixed(2)
            self.state.title = action_title
        }
        catch (el) {
            window.location.href;
        }
    }
    async printPdf(ev) {
        ev.preventDefault();
        var self = this;
        let totals = {
            'total_debit':this.state.total_debit,
            'total_credit':this.state.total_credit,
            'currency':this.state.currency,
        }
        var action_title = self.props.action.display_name;
        return self.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'dynamic_accounts_report.general_ledger',
            'report_file': 'dynamic_accounts_report.general_ledger',
            'data': {
                'account': self.state.account,
                'data': self.state.account_data,
                'total': self.state.account_total,
                'title': action_title,
                'filters': this.filter(),
                'grand_total': totals,
                'report_name': self.props.action.display_name
            },
            'display_name': self.props.action.display_name,
        });
    }
    async print_xlsx() {
        var self = this;
        let totals = {
            'total_debit':this.state.total_debit,
            'total_credit':this.state.total_credit,
            'currency':this.state.currency,
        }
        var action_title = self.props.action.display_name;
        var datas = {
            'account': self.state.account,
            'data': self.state.account_data,
            'total': self.state.account_total,
            'title': action_title,
            'filters': this.filter(),
            'grand_total': totals,
        }
        var action = {
            'data': {
                'model': 'account.general.ledger',
                'data': JSON.stringify(datas),
                'output_format': 'xlsx',
                'report_name': action_title,
            },
        };
        BlockUI;
        await download({
            url: '/xlsx_report',
            data: action.data,
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
    gotoJournalEntry(ev) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'account.move',
            res_id: parseInt(ev.target.attributes["data-id"].value, 10),
            views: [[false, "form"]],
            target: "current",
        });
    }
    gotoJournalItem(ev) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'account.move.line',
            name: "Journal Items",
            views: [[false, "list"]],
            domain: [["account_id", "=", parseInt(ev.target.attributes["data-id"].value, 10)]],
            target: "current",
        });
    }
    getDomain() {
        return [];
    }
    async applyFilter(val, ev, is_delete = false) {
        let account_list = []
        let account_totals = ''
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        this.state.account = null
        this.state.account_data = null
        this.state.account_total = null
        this.state.filter_applied = true;
        if (ev) {
            if (ev.input && ev.input.attributes.placeholder.value == 'Account' && !is_delete) {
                this.state.selected_analytic.push(val[0].id)
                this.state.selected_analytic_account_rec.push(val[0])
            } else if (is_delete) {
                let index = this.state.selected_analytic_account_rec.indexOf(val)
                this.state.selected_analytic_account_rec.splice(index, 1)
                this.state.selected_analytic = this.state.selected_analytic_account_rec.map((rec) => rec.id)
            }
        }
        else {
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
            } else if (val.target.attributes["data-value"].value == 'month') {
                this.state.date_range = val.target.attributes["data-value"].value
            } else if (val.target.attributes["data-value"].value == 'year') {
                this.state.date_range = val.target.attributes["data-value"].value
            } else if (val.target.attributes["data-value"].value == 'quarter') {
                this.state.date_range = val.target.attributes["data-value"].value
            } else if (val.target.attributes["data-value"].value == 'last-month') {
                this.state.date_range = val.target.attributes["data-value"].value
            } else if (val.target.attributes["data-value"].value == 'last-year') {
                this.state.date_range = val.target.attributes["data-value"].value
            } else if (val.target.attributes["data-value"].value == 'last-quarter') {
                this.state.date_range = val.target.attributes["data-value"].value
            }
            else if (val.target.attributes["data-value"].value == 'journal') {
                if (!val.target.classList.contains("selected-filter")) {
                    this.state.selected_journal_list.push(parseInt(val.target.attributes["data-id"].value, 10))
                    val.target.classList.add("selected-filter");
                } else {
                    const updatedList = this.state.selected_journal_list.filter(item => item !== parseInt(val.target.attributes["data-id"].value, 10));
                    this.state.selected_journal_list = updatedList
                    val.target.classList.remove("selected-filter");
                }
            }

            else if (val.target.attributes["data-value"].value == 'analytic') {
                if (!val.target.classList.contains("selected-filter")) {
                    this.state.selected_analytic_list.push(parseInt(val.target.attributes["data-id"].value, 10))
                    val.target.classList.add("selected-filter");
                } else {
                    const updatedList = this.state.selected_analytic_list.filter(item => item !== parseInt(val.target.attributes["data-id"].value, 10));
                    this.state.selected_analytic_list = updatedList
                    val.target.classList.remove("selected-filter");
                }
            }
            else if (val.target.attributes["data-value"].value == 'journal') {

                if (!val.target.classList.contains("selected-filter")) {
                    this.state.selected_journal_list.push(parseInt(val.target.attributes["data-id"].value, 10))
                    val.target.classList.add("selected-filter");
                } else {
                    const updatedList = this.state.selected_journal_list.filter(item => item !== parseInt(val.target.attributes["data-id"].value, 10));
                    this.state.selected_journal_list = updatedList
                    val.target.classList.remove("selected-filter");
                }
            }
            else if (val.target.attributes["data-value"].value == 'analytic') {
                if (!val.target.classList.contains("selected-filter")) {
                    this.state.selected_analytic_list.push(parseInt(val.target.attributes["data-id"].value, 10))
                    val.target.classList.add("selected-filter");
                } else {
                    const updatedList = this.state.selected_analytic_list.filter(item => item !== parseInt(val.target.attributes["data-id"].value, 10));
                    this.state.selected_analytic_list = updatedList
                    val.target.classList.remove("selected-filter");
                }
            }
            else if (val.target.attributes["data-value"].value === 'draft') {
                if (val.target.classList.contains("selected-filter")) {
                    const { draft, ...updatedAccount } = this.state.options;
                    this.state.options = updatedAccount;
                    val.target.classList.remove("selected-filter");
                } else {
                    this.state.options = {
                        ...this.state.options,
                        'draft': true
                    };
                    val.target.classList.add("selected-filter");
                }
            }else if (val.target.attributes["data-value"].value === 'cash-basis') {
                if (val.target.classList.contains("selected-filter")) {
                    const { cash, ...updatedAccount } = this.state.method;
                    this.state.method = updatedAccount;
                    this.state.method = {
                        ...this.state.method,
                        'accrual': true
                    }
                    val.target.classList.remove("selected-filter");
                } else {
                    const { accrual, ...updatedAccount } = this.state.method;
                    this.state.method = updatedAccount;
                    this.state.method = {
                        ...this.state.method,
                        'cash': true
                    };
                    val.target.classList.add("selected-filter");
                }
            }
        }
        let filtered_data = await this.orm.call("account.general.ledger", "get_filter_values", [this.state.selected_journal_list, this.state.date_range, this.state.options, this.state.selected_analytic_list,this.state.method]);
        $.each(filtered_data, function (index, value) {
            if (index !== 'account_totals' && index !== 'journal_ids' && index !== 'analytic_ids') {
                account_list.push(index)
            }
            else {
                account_totals = value
                Object.values(account_totals).forEach(account_list => {
                        totalDebitSum += account_list.total_debit || 0;
                        totalCreditSum += account_list.total_credit || 0;
                    });
            }
        })
        this.state.account = account_list
        this.state.account_data = filtered_data
        this.state.account_total = account_totals
        this.state.total_debit = totalDebitSum.toFixed(2)
        this.state.total_credit = totalCreditSum.toFixed(2)
        if ($(this.unfoldButton.el.classList).find("selected-filter")) {
            this.unfoldButton.el.classList.remove("selected-filter")
        }
    }
    async unfoldAll(ev) {
        if (!ev.target.classList.contains("selected-filter")) {
            for (var length = 0; length < this.tbody.el.children.length; length++) {
                $(this.tbody.el.children[length])[0].classList.add('show')
            }
            ev.target.classList.add("selected-filter");
        } else {
            for (var length = 0; length < this.tbody.el.children.length; length++) {
                $(this.tbody.el.children[length])[0].classList.remove('show')
            }
            ev.target.classList.remove("selected-filter");
        }
    }
    filter() {
    var self=this;
    let startDate, endDate;
    let startYear, startMonth, startDay, endYear, endMonth, endDay;
        if (self.state.date_range){
            const today = new Date();
            if (self.state.date_range === 'year') {
                startDate = new Date(today.getFullYear(), 0, 1);
                endDate = new Date(today.getFullYear(), 11, 31);
            } else if (self.state.date_range === 'quarter') {
                const currentQuarter = Math.floor(today.getMonth() / 3);
                startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
                endDate = new Date(today.getFullYear(), (currentQuarter + 1) * 3, 0);
            } else if (self.state.date_range === 'month') {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            } else if (self.state.date_range === 'last-month') {
                startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                endDate = new Date(today.getFullYear(), today.getMonth(), 0);
            } else if (self.state.date_range === 'last-year') {
                startDate = new Date(today.getFullYear() - 1, 0, 1);
                endDate = new Date(today.getFullYear() - 1, 11, 31);
            } else if (self.state.date_range === 'last-quarter') {
                const lastQuarter = Math.floor((today.getMonth() - 3) / 3);
                startDate = new Date(today.getFullYear(), lastQuarter * 3, 1);
                endDate = new Date(today.getFullYear(), (lastQuarter + 1) * 3, 0);
            }
            else{
                startDate = new Date(self.state.date_range.start_date);
                endDate = new Date(self.state.date_range.end_date);
            }
        // Get the date components for start and end dates
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
        const selectedJournalIDs = Object.values(self.state.selected_journal_list);
        const selectedJournalNames = selectedJournalIDs.map((journalID) => {
          const journal = self.state.journals.find((journal) => journal.id === journalID);
          return journal ? journal.name : '';
        });
        const selectedAnalyticIDs = Object.values(self.state.selected_analytic_list);
        const selectedAnalyticNames = selectedAnalyticIDs.map((analyticID) => {
          const analytic = self.state.analytics.find((analytic) => analytic.id === analyticID);
          return analytic ? analytic.name : '';
        });
        let filters = {
            'journal': selectedJournalNames,
            'analytic': selectedAnalyticNames,
            'account': self.state.selected_analytic_account_rec,
            'options': self.state.options,
            'start_date': null,
            'end_date': null,
        };
        // Check if start and end dates are available before adding them to the filters object
        if (startYear !== undefined && startMonth !== undefined && startDay !== undefined &&
            endYear !== undefined && endMonth !== undefined && endDay !== undefined) {
            filters['start_date'] = `${startYear}-${startMonth < 10 ? '0' : ''}${startMonth}-${startDay < 10 ? '0' : ''}${startDay}`;
            filters['end_date'] = `${endYear}-${endMonth < 10 ? '0' : ''}${endMonth}-${endDay < 10 ? '0' : ''}${endDay}`;
        }
        return filters
    }
}
GeneralLedger.defaultProps = {
    resIds: [],
};
GeneralLedger.template = 'gl_template_new';
actionRegistry.add("gen_l", GeneralLedger);
