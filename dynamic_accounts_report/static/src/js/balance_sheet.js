/** @odoo-module **/
import { Component, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";

const now = new Date();
const actionRegistry = registry.category("actions");

export class BalanceSheet extends Component {
    static template = 'bls_template_new';

    date_from = signal.ref();
    date_to = signal.ref();
    period = signal.ref();
    period_year = signal.ref();
    posted = signal.ref();
    draft = signal.ref();
    unfoldButton = signal.ref();
    tbody = signal.ref();

    setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');

        this.state = proxy({
            data: null,
            datas: null,
            filter_data: null,
            year: [now.getFullYear()],
            comparison: false,
            comparison_type: null,
            date_range: null,
            date_from: null,
            date_to: null,
            journal_ids: [],
            account_ids: [],
            analytic_ids: [],
            target_move: "posted",
            title: "Balance Sheet",
        });

        this.initData();
    }

    async initData() {
        this.wizard_id = (await this.orm.call("dynamic.balance.sheet.report", "create", [{}])) || null;
        await this.load_data(true);
    }

    async load_data(initialRender = false) {
        const action_title = this.props?.action?.display_name || "Balance Sheet";
        try {
            let data = await this.orm.call("dynamic.balance.sheet.report", "view_report", [
                this.wizard_id,
                this.state.comparison,
                this.state.comparison_type,
            ]);
            this.state.data = data[0];
            this.state.filter_data = data[1];
            this.state.datas = data[2];
            this.state.title = action_title;
        } catch (el) {
            console.error(el);
        }
    }

    async show_gl(ev) {
        return this.action.doAction({
            type: 'ir.actions.client',
            name: 'General Ledger',
            tag: 'gen_l',
        });
    }

    async print_pdf(ev) {
        ev.preventDefault();
        let data = await this.orm.call("dynamic.balance.sheet.report", "view_report", [
            this.wizard_id,
            this.state.comparison,
            this.state.comparison_type,
        ]);
        this.state.data = data[0];
        this.state.datas = data[2];

        const statePlain = JSON.parse(JSON.stringify(this.state));
        const reportName = this.props?.action?.display_name || "Balance Sheet";

        const actionPayload = {
            type: 'ir.actions.report',
            report_type: 'qweb-pdf',
            report_name: 'dynamic_accounts_report.balance_sheet',
            report_file: 'dynamic_accounts_report.balance_sheet',
            data: {
                ...statePlain,
                data: statePlain.data || data[0] || {},
                datas: statePlain.datas || data[2] || [],
                year: statePlain.year || [now.getFullYear()],
                account_ids: this.state.account_ids || [],
                journal_ids: this.state.journal_ids || [],
                analytic_ids: this.state.analytic_ids || [],
                target: this.state.target_move || "",
                date_from: this.state.date_from || "",
                date_to: this.state.date_to || "",
                date_range: this.state.date_range || "",
                comparison: this.state.comparison || "",
                comparison_type: this.state.comparison_type || "",
                report_name: reportName,
            },
            display_name: reportName,
        };
        return this.action.doAction(actionPayload);
    }

    async print_xlsx(ev) {
        let data = await this.orm.call("dynamic.balance.sheet.report", "view_report", [
            this.wizard_id,
            this.state.comparison,
            this.state.comparison_type,
        ]);
        this.state.data = data[0];
        this.state.datas = data[2];
        var action = {
            'data': {
                'model': 'dynamic.balance.sheet.report',
                'data': JSON.stringify(this.state),
                'output_format': 'xlsx',
                'report_name': this.props?.action?.display_name || "Balance Sheet",
                'report_action': this.props?.action?.xml_id,
            },
        };
        await download({
            url: '/dynamic_account/xlsx_report',
            data: action.data,
        });
    }

    async apply_journal(ev) {
        ev.target.classList.toggle("selected-filter");
        const journalId = ev.target.getAttribute("data-id") || ev.target.querySelector("span")?.getAttribute("data-id");
        const journalName = ev.target.querySelector("span")?.textContent?.trim();

        this.filter = { journal_ids: journalId || journalName };
        let res = await this.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        if (ev.delegateTarget.querySelector('.code')) {
            ev.delegateTarget.querySelector('.code').innerHTML = res[0].journal_ids;
        }
        this.initial_render = false;
        await this.load_data(this.initial_render);
    }

    async apply_account(ev) {
        ev.target.classList.toggle("selected-filter");
        const accountId = ev.target.getAttribute("data-id") || ev.target.querySelector("span")?.getAttribute("data-id");
        const domAccountName = ev.target.querySelector("span")?.textContent?.trim();

        this.filter = { account_ids: accountId || domAccountName };
        let res = await this.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        if (ev.delegateTarget.querySelector('.account')) {
            ev.delegateTarget.querySelector('.account').innerHTML = res[0].account_ids;
        }
        this.initial_render = false;
        await this.load_data(this.initial_render);
    }

    async apply_analytic_accounts(ev) {
        ev.target.classList.toggle("selected-filter");
        const analyticName = ev.target.querySelector("span")?.textContent?.trim();
        const analyticId = ev.target.getAttribute("data-id") || ev.target.querySelector("span")?.getAttribute("data-id");

        this.filter = { analytic_ids: analyticId || analyticName };
        let res = await this.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        if (ev.delegateTarget.querySelector('.analytic')) {
            ev.delegateTarget.querySelector('.analytic').innerHTML = res[0].analytic_ids;
        }
        this.initial_render = false;
        await this.load_data(this.initial_render);
    }

    async apply_entries(ev) {
        ev.target.classList.add('selected-filter');
        const postedEl = this.posted();
        const draftEl = this.draft();
        if (ev.target.value === 'draft') {
            if (postedEl) postedEl.classList.remove('selected-filter');
        } else {
            if (draftEl) draftEl.classList.remove('selected-filter');
        }
        this.filter = { 'target': ev.target.value };
        let res = await this.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        if (ev.delegateTarget.querySelector('.target')) {
            ev.delegateTarget.querySelector('.target').innerHTML = res[0].target_move;
        }
        this.initial_render = false;
        await this.load_data(this.initial_render);
    }

    async unfoldAll(ev) {
        const tbodyEl = this.tbody();
        if (!tbodyEl) return;
        if (!ev.target.classList.contains("selected-filter")) {
            for (let length = 0; length < tbodyEl.children.length; length++) {
                tbodyEl.children[length].classList.add('show');
            }
            ev.target.classList.add("selected-filter");
        } else {
            for (let length = 0; length < tbodyEl.children.length; length++) {
                tbodyEl.children[length].classList.remove('show');
            }
            ev.target.classList.remove("selected-filter");
        }
    }

    async apply_date(ev) {
        if (ev.target.name === 'start_date') {
            this.filter = { ...this.filter, date_from: ev.target.value };
            this.state.date_from = ev.target.value;
        } else if (ev.target.name === 'end_date') {
            this.filter = { ...this.filter, date_to: ev.target.value };
            this.state.date_to = ev.target.value;
        } else {
            const dataVal = ev.target.getAttribute("data-value");
            if (dataVal) {
                this.filter = dataVal;
                this.state.date_range = dataVal;
            }
        }
        await this.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        this.initial_render = false;
        await this.load_data(this.initial_render);
    }

    onPeriodChange(ev) {
        const periodYearEl = this.period_year();
        if (periodYearEl) {
            periodYearEl.value = ev.target.value;
        }
    }

    onPeriodYearChange(ev) {
        const periodEl = this.period();
        if (periodEl) {
            periodEl.value = ev.target.value;
        }
    }

    async applyComparisonPeriod() {
        const periodEl = this.period();
        if (!periodEl) return;
        this.state.comparison = periodEl.value;
        this.state.comparison_type = "month";
        let monthNamesShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        let res = await this.orm.call("dynamic.balance.sheet.report", "comparison_filter", [this.wizard_id, this.state.comparison]);
        this.state.year = [monthNamesShort[now.getMonth()] + '  ' + now.getFullYear()];
        for (let length = 0; length < res.length; length++) {
            const dateObject = new Date(res[length]['date_to']);
            this.state.year.push(monthNamesShort[dateObject.getMonth()] + '  ' + dateObject.getFullYear());
        }
        await this.load_data(this.initial_render);
    }

    async applyComparisonYear() {
        const periodYearEl = this.period_year();
        if (!periodYearEl) return;
        this.state.comparison = periodYearEl.value;
        this.state.comparison_type = "year";
        let res = await this.orm.call("dynamic.balance.sheet.report", "comparison_filter_year", [this.wizard_id, this.state.comparison]);
        this.state.year = [now.getFullYear()];
        for (let length = 0; length < res.length; length++) {
            const dateObject = new Date(res[length]['date_to']);
            this.state.year.push(dateObject.getFullYear());
        }
        await this.load_data(this.initial_render);
    }

    apply_comparison() {
        this.state.comparison = false;
        this.state.comparison_type = null;
        this.state.year = [now.getFullYear()];
    }
}

actionRegistry.add("bl_s", BalanceSheet);