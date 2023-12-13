/** @odoo-module **/
const { Component } = owl;
const now = new Date();
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");

class ProfitAndLoss extends owl.Component {
    async setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.tbody = useRef('tbody');
        this.posted = useRef('posted');
        this.period = useRef('periods');
        this.period_year = useRef('period_year');
        this.draft = useRef('draft');
        this.state = useState({
            data: null,
            filter_data: null,
            year : [now.getFullYear()],
            comparison: false,
            comparison_type: null,
        });
        this.wizard_id = await this.orm.call("dynamic.balance.sheet.report", "create", [{}]) | null;
        this.load_data(self.initial_render = true);
    }
    async load_data() {
        /**
         * Loads the data for the profit and loss report.
         */
        var self = this;
        var action_title = self.props.action.display_name;
        try {
            var self = this;
            let data = await self.orm.call("dynamic.balance.sheet.report", "view_report", [this.wizard_id,this.state.comparison,this.state.comparison_type]);
            self.state.data = data[0]
            self.state.datas = data[2]
            self.state.filter_data = data[1]
            self.state.title = action_title
        }
        catch (el) {
            window.location.href
        }
    }
    async print_pdf(ev) {
        /**
         * Generates and displays a PDF report based on the profit and loss data.
         *
         * @param {Event} ev - The event object triggered by the action.
         * @returns {Promise} - A promise that resolves to the result of the action.
         */
        ev.preventDefault();
        var self = this;
        let data = await self.orm.call("dynamic.balance.sheet.report", "view_report", [this.wizard_id,this.state.comparison,this.state.comparison_type]);
        self.state.data = data[0];
        self.state.datas = data[2];
        return self.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'dynamic_accounts_report.profit_loss',
            'report_file': 'dynamic_accounts_report.profit_loss',
            'data': {
                'data': self.state,
                'report_name': self.props.action.display_name
            },
            'display_name': self.props.action.display_name,
        });
    }
    async print_xlsx(ev) {
        /**
         * Generates and downloads an XLSX report based on the profit and loss data.
         *
         * @param {Event} ev - The event object triggered by the action.
         */
        var self = this;
        let data = await self.orm.call("dynamic.balance.sheet.report", "view_report", [this.wizard_id,this.state.comparison,this.state.comparison_type]);
        self.state.data = data[0];
        self.state.datas = data[2];

        var action = {
            'data': {
                'model': 'dynamic.balance.sheet.report',
                'data': JSON.stringify(self.state),
                'output_format': 'xlsx',
                'report_name': self.props.action.display_name,
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
    async apply_journal(ev) {
        /**
        * Applies journal filtering based on the selected option in an event target.
        *
        * @param {Event} ev - The event object triggered by the action.
        */
        self = this;
        // Toggle the 'selected-filter' class on the event target
        if (ev.target.classList.contains("selected-filter")) {
            ev.target.classList.remove('selected-filter');
        } else {
            ev.target.classList.add('selected-filter');
        }
        // Set the filter object with the 'journal_ids' based on the content of the target span
        this.filter = {
            'journal_ids': ev.target.querySelector('span').textContent,
        };
        // Call the 'dynamic.balance.sheet.report' method with the filter parameter
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        // Update the innerHTML of the code target element with the result value
        ev.delegateTarget.querySelector('.code').innerHTML = res[0].journal_ids;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async apply_account(ev) {
        /**
        * Applies account filtering based on the selected option in an event target.
        *
        * @param {Event} ev - The event object triggered by the action.
        */
        self = this;
        // Toggle the 'selected-filter' class on the event target
        if (ev.target.classList.contains("selected-filter")) {
            ev.target.classList.remove('selected-filter');
        } else {
            ev.target.classList.add('selected-filter');
        }
        // Set the filter object with the 'account_ids' based on the content of the target span
        this.filter = {
            'account_ids': ev.target.querySelector('span').textContent,
        };
        // Call the 'dynamic.balance.sheet.report' method with the filter parameter
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        // Update the innerHTML of the account target element with the result value
        ev.delegateTarget.querySelector('.account').innerHTML = res[0].account_ids;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async show_gl(ev) {
        /**
        * Shows the General Ledger view by triggering an action.
        *
        * @param {Event} ev - The event object triggered by the action.
        * @returns {Promise} - A promise that resolves to the result of the action.
        */
        return this.action.doAction({
            type: 'ir.actions.client',
            name: 'General Ledger',
            tag: 'gen_l',
        });
    }
    async apply_analytic_accounts(ev) {
        /**
         * Applies analytic accounts filtering based on the selected option in an event target.
         *
         * @param {Event} ev - The event object triggered by the action.
         */
        self = this;
        // Toggle the 'selected-filter' class on the event target
        if (ev.target.classList.contains("selected-filter")) {
            ev.target.classList.remove('selected-filter');
        } else {
            ev.target.classList.add('selected-filter');
        }
        // Set the filter object with the 'analytic_ids' based on the content of the target span
        this.filter = {
            'analytic_ids': ev.target.querySelector('span').textContent,
        };
        // Call the 'dynamic.balance.sheet.report' method with the filter parameter
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        // Update the innerHTML of the analytic target element with the result value
        ev.delegateTarget.querySelector('.analytic').innerHTML = res[0].analytic_ids;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async apply_entries(ev) {
        /**
     * Applies entries filtering based on the selected option in an event target.
     *
     * @param {Event} ev - The event object triggered by the action.
     */
        self = this;
        // Add 'selected-filter' class to the event target
        ev.target.classList.add('selected-filter');
        if (ev.target.value == 'draft') {
            // Remove 'selected-filter' class from the 'posted' element
            this.posted.el.classList.remove('selected-filter');
        } else {
            // Remove 'selected-filter' class from the 'draft' element
            this.draft.el.classList.remove('selected-filter');
        }
        // Set the filter object based on the target value
        this.filter = {
            'target': ev.target.value
        };
        // Call the 'dynamic.balance.sheet.report' method with the filter parameter
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        // Update the innerHTML of the target element with the result value
        ev.delegateTarget.querySelector('.target').innerHTML = res[0].target_move;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async unfoldAll(ev) {
        /**
         * Unfolds or collapses all elements in a table body based on the given event target's class.
         *
         * @param {Event} ev - The event object triggered by the action.
         */
        if (!ev.target.classList.contains("selected-filter")) {
            // Unfold all elements
            for (var length = 0; length < this.tbody.el.children.length; length++) {
                $(this.tbody.el.children[length])[0].classList.add('show')
            }
            ev.target.classList.add("selected-filter");
        } else {
            // Collapse all elements
            for (var length = 0; length < this.tbody.el.children.length; length++) {
                $(this.tbody.el.children[length])[0].classList.remove('show')
            }
            ev.target.classList.remove("selected-filter");
        }
    }
    async apply_date(ev){
    /**
     * Applies the selected date filter and triggers data loading based on the selected filter value.
     * @param {Event} ev - The event object triggered by the date selection.
     * @returns {Promise<void>} - A promise that resolves when the data is loaded.
     */
        self = this
        if (ev.target.name === 'start_date') {
                this.filter = {
                    ...this.filter,
                    date_from: ev.target.value
                };
        } else if (ev.target.name === 'end_date') {
                this.filter = {
                    ...this.filter,
                    date_to: ev.target.value
                };
        } else if (ev.target.attributes["data-value"].value == 'month') {
                this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'year') {
                this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'quarter') {
            this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'last-month') {
            this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'last-year') {
            this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'last-quarter') {
            this.filter = ev.target.attributes["data-value"].value
        }
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        self.initial_render = false;
        this.load_data(this.initial_render);
    }
    onPeriodChange(ev){
        this.period_year.el.value = ev.target.value
    }
    onPeriodYearChange(ev){
        this.period.el.value = ev.target.value
    }
    async applyComparisonPeriod(){
        this.state.comparison  = this.period.el.value
        this.state.comparison_type = "month"
        let monthNamesShort = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ]
        let res = await this.orm.call("dynamic.balance.sheet.report", "comparison_filter", [this.wizard_id, this.state.comparison]);
        this.state.year = [monthNamesShort[now.getMonth()]+'  ' + now.getFullYear()]
        for (var length = 0; length < res.length; length++) {
                const dateObject = new Date(res[length]['date_to']);
                this.state.year.push(monthNamesShort[dateObject.getMonth()]+'  ' + dateObject.getFullYear())
            }
        this.load_data(self.initial_render);
    }
    sumGrossProfit(op_inc, cor) {
        /**
         * Calculates the sum of values in an array of objects by a specified key.
         *
         * @param {Array} data - Array of objects containing numeric values.
         * @param {string} key - The key to access the numeric value in each object.
         * @returns {number} The sum of the numeric values.
         */
         const stringValue = cor;
         const floatValue = parseFloat(stringValue.replace(/,/g, ''));
        return parseFloat(op_inc) + floatValue;
    }
    async applyComparisonYear(){
        this.state.comparison = this.period_year.el.value
        this.state.comparison_type = "year"
        let res = await this.orm.call("dynamic.balance.sheet.report", "comparison_filter_year", [this.wizard_id, this.state.comparison]);
        this.state.year = [now.getFullYear()]
        for (var length = 0; length < res.length; length++) {
                const dateObject = new Date(res[length]['date_to']);
                this.state.year.push(dateObject.getFullYear())
            }
        this.load_data(self.initial_render);
    }
    apply_comparison() {
    this.state.comparison = false
    this.state.comparison_type = null
     this.state.year = [now.getFullYear()]
    }
}
ProfitAndLoss.template = 'dfr_template_new';
actionRegistry.add("dfr_n", ProfitAndLoss);
