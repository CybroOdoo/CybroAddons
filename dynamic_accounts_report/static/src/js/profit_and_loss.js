/** @odoo-module **/

import { Component, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";

const actionRegistry = registry.category("actions");
const now = new Date();

export class ProfitAndLoss extends Component {
    static template = "dfr_template_new";

    // Declare all template refs as class fields
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
        this.orm = useService("orm");
        this.action = useService("action");

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
            title: "Profit and Loss Report",
        });

        this.initData();
    }

    async initData() {
        this.wizard_id = (await this.orm.call("dynamic.balance.sheet.report", "create", [{}])) || null;
        await this.load_data(true);
    }

    async load_data(initialRender = false) {
        const action_title = this.props?.action?.display_name || "Profit and Loss Report";
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
        const reportName = this.props?.action?.display_name || "Profit and Loss";
        const now = new Date();

        const actionPayload = {
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "dynamic_accounts_report.profit_loss",
            report_file: "dynamic_accounts_report.profit_loss",
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

    _getFilters() {
        const today = new Date();
        let startDate = null,
            endDate = null;

        if (this.state.date_range) {
            const currentMonth = today.getMonth();
            const currentYear = today.getFullYear();

            switch (this.state.date_range) {
                case "year":
                    startDate = new Date(currentYear, 0, 1);
                    endDate = new Date(currentYear, 11, 31);
                    break;
                case "quarter":
                    const currentQuarter = Math.floor(currentMonth / 3);
                    startDate = new Date(currentYear, currentQuarter * 3, 1);
                    endDate = new Date(currentYear, (currentQuarter + 1) * 3, 0);
                    break;
                case "month":
                    startDate = new Date(currentYear, currentMonth, 1);
                    endDate = new Date(currentYear, currentMonth + 1, 0);
                    break;
                case "last-month":
                    startDate = new Date(currentYear, currentMonth - 1, 1);
                    endDate = new Date(currentYear, currentMonth, 0);
                    break;
                case "last-year":
                    startDate = new Date(currentYear - 1, 0, 1);
                    endDate = new Date(currentYear - 1, 11, 31);
                    break;
                case "last-quarter":
                    const lastQuarter = Math.floor((currentMonth - 3) / 3);
                    startDate = new Date(currentYear, lastQuarter * 3, 1);
                    endDate = new Date(currentYear, (lastQuarter + 1) * 3, 0);
                    break;
            }
        }

        const formatDate = (d) => {
            if (!d) return null;
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, "0");
            const day = String(d.getDate()).padStart(2, "0");
            return `${y}-${m}-${day}`;
        };

        return {
            date_range: this.state.date_range || null,
            date_from: formatDate(startDate),
            date_to: formatDate(endDate),
            journal_ids:
                this.state.journal_ids && this.state.journal_ids.length
                    ? this.state.journal_ids.map((j) => j.name).join(", ")
                    : null,
            account_ids:
                this.state.account_ids && this.state.account_ids.length
                    ? this.state.account_ids.map((a) => a.name).join(", ")
                    : null,
            analytic_ids:
                this.state.analytic_ids && this.state.analytic_ids.length
                    ? this.state.analytic_ids.map((a) => a.name).join(", ")
                    : null,
            target: this.state.target_move || "posted",
            comparison: this.state.comparison || null,
            comparison_type: this.state.comparison_type || null,
        };
    }

    async print_xlsx(ev) {
        let data = await this.orm.call("dynamic.balance.sheet.report", "view_report", [
            this.wizard_id,
            this.state.comparison,
            this.state.comparison_type,
        ]);
        this.state.data = data[0];
        this.state.datas = data[2];

        const action = {
            data: {
                model: "dynamic.balance.sheet.report",
                data: JSON.stringify(this.state),
                output_format: "xlsx",
                report_action: this.props?.action?.xml_id,
                report_name: this.props?.action?.display_name,
            },
        };

        await download({
            url: "/dynamic_account/xlsx_report",
            data: action.data,
        });
    }

    async apply_journal(ev) {
        ev.target.classList.toggle("selected-filter");

        const journalId =
            ev.target.getAttribute("data-id") ||
            ev.target.querySelector("span")?.getAttribute("data-id");
        const journalName = ev.target.querySelector("span")?.textContent?.trim();

        this.filter = { journal_ids: journalId || journalName };

        let res = await this.orm.call("dynamic.balance.sheet.report", "filter", [
            this.wizard_id,
            this.filter,
        ]);

        if (ev.delegateTarget.querySelector(".code")) {
            ev.delegateTarget.querySelector(".code").innerHTML = res[0].journal_ids;
        }
        this.initial_render = false;
        this.load_data(this.initial_render);

        if (!Array.isArray(this.state.journal_ids)) {
            this.state.journal_ids = [];
        }

        const journalNames = (res || [])
            .map((r) => (r.journal_ids || []).flat())
            .flat()
            .filter((n) => typeof n === "string");

        if (ev.target.classList.contains("selected-filter")) {
            for (const jName of journalNames) {
                if (!this.state.journal_ids.includes(jName)) {
                    this.state.journal_ids.push(jName);
                }
            }
        } else {
            this.state.journal_ids = this.state.journal_ids.filter((j) => !journalNames.includes(j));
        }

        this.state.journal_ids = this.state.journal_ids.flat();
    }

    async apply_account(ev) {
        ev.target.classList.toggle("selected-filter");

        const accountId =
            ev.target.getAttribute("data-id") ||
            ev.target.querySelector("span")?.getAttribute("data-id") ||
            null;
        const domAccountName = ev.target.querySelector("span")?.textContent?.trim() || null;

        this.filter = { account_ids: accountId || domAccountName };

        const res = await this.orm.call("dynamic.balance.sheet.report", "filter", [
            this.wizard_id,
            this.filter,
        ]);

        try {
            if (ev.delegateTarget.querySelector(".account")) {
                ev.delegateTarget.querySelector(".account").innerHTML = res[0].account_ids;
            }
        } catch (e) {
            // ignore
        }
        this.initial_render = false;
        this.load_data(this.initial_render);

        const normalizeAccountNames = (raw) => {
            if (!raw) return [];
            if (Array.isArray(raw)) {
                const itemWithKey = raw.find((item) => item && item.account_ids !== undefined);
                const item = itemWithKey || raw[0];
                if (!item) return [];
                const val = item.account_ids !== undefined ? item.account_ids : item;

                if (Array.isArray(val) && val.every((v) => typeof v === "string")) {
                    return val;
                }
                if (Array.isArray(val)) {
                    const flattened = val.flat(Infinity).filter((v) => typeof v === "string");
                    if (flattened.length) return flattened;
                }
                if (typeof val === "string") {
                    return val.split(",").map((s) => s.trim()).filter(Boolean);
                }
                return raw.flat(Infinity).filter((x) => typeof x === "string");
            }
            if (typeof raw === "string") {
                return raw.split(",").map((s) => s.trim()).filter(Boolean);
            }
            return [];
        };

        const accountNames = normalizeAccountNames(res);
        const finalNames = accountNames && accountNames.length ? accountNames : domAccountName ? [domAccountName] : [];

        if (!Array.isArray(this.state.account_ids)) this.state.account_ids = [];

        if (ev.target.classList.contains("selected-filter")) {
            finalNames.forEach((name) => {
                if (!this.state.account_ids.includes(name)) {
                    this.state.account_ids.push(name);
                }
            });
        } else {
            this.state.account_ids = this.state.account_ids.filter((n) => !finalNames.includes(n));
        }

        this.state.account_ids = this.state.account_ids.flat();
    }

    async show_gl(ev) {
        return this.action.doAction({
            type: "ir.actions.client",
            name: "General Ledger",
            tag: "gen_l",
        });
    }

getNonZeroAccounts(key) {
    try {
        if (!this.state.datas || !Array.isArray(this.state.datas) || !this.state.datas[0]) {
            return [];
        }
        const first = this.state.datas[0][key];
        if (!first || !Array.isArray(first[0])) {
            return [];
        }
        const baseAccounts = first[0];
        return baseAccounts.filter((acc) => {
            if (!acc || acc.account_id === undefined) return false;
            return this.state.datas.some((period) => {
                const arr = period && period[key] && period[key][0];
                if (!Array.isArray(arr)) return false;
                const match = arr.find((a) => a.account_id === acc.account_id);
                return match && match.amount !== '0.00';
            });
        });
    } catch (e) {
        console.error('[getNonZeroAccounts ERROR]', key, e);
        return [];
    }
}

getAmountFor(key, period, accountId) {
    try {
        const arr = period && period[key] && period[key][0];
        if (!Array.isArray(arr)) return '';
        const match = arr.find((a) => a.account_id === accountId);
        return match ? match.amount : '';
    } catch (e) {
        console.error('[getAmountFor ERROR]', key, e);
        return '';
    }
}

toggleCategory(ev) {
    const el = ev.target.closest('[data-category]');
    const cat = el ? el.getAttribute('data-category') : null;
    if (!cat) return;
    const rows = document.querySelectorAll('.cat-' + cat);
    rows.forEach((row) => row.classList.toggle('show'));
}

    async apply_analytic_accounts(ev) {
        ev.target.classList.toggle("selected-filter");

        const analyticName = ev.target.querySelector("span")?.textContent?.trim();
        const analyticId =
            ev.target.getAttribute("data-id") ||
            ev.target.querySelector("span")?.getAttribute("data-id");

        this.filter = { analytic_ids: analyticId || analyticName };

        let res = await this.orm.call("dynamic.balance.sheet.report", "filter", [
            this.wizard_id,
            this.filter,
        ]);

        if (ev.delegateTarget.querySelector(".analytic")) {
            ev.delegateTarget.querySelector(".analytic").innerHTML = res[0].analytic_ids;
        }
        this.initial_render = false;
        this.load_data(this.initial_render);

        if (!Array.isArray(this.state.analytic_ids)) {
            this.state.analytic_ids = [];
        }

        const analyticNames = res
            ?.map((r) => (r.analytic_ids ? r.analytic_ids : []))
            .flat()
            .filter(Boolean);

        if (ev.target.classList.contains("selected-filter")) {
            analyticNames.forEach((name) => {
                if (!this.state.analytic_ids.includes(name)) {
                    this.state.analytic_ids.push(name);
                }
            });
        } else {
            this.state.analytic_ids = this.state.analytic_ids.filter(
                (n) => !analyticNames.includes(n)
            );
        }
    }

    async apply_entries(ev) {
        ev.target.classList.add("selected-filter");

        // Use signal refs as functions to get DOM elements
        const postedEl = this.posted();
        const draftEl = this.draft();

        if (ev.target.value === "draft") {
            if (postedEl) postedEl.classList.remove("selected-filter");
        } else {
            if (draftEl) draftEl.classList.remove("selected-filter");
        }

        this.filter = {
            target: ev.target.value,
        };

        let res = await this.orm.call("dynamic.balance.sheet.report", "filter", [
            this.wizard_id,
            this.filter,
        ]);

        if (ev.delegateTarget.querySelector(".target")) {
            ev.delegateTarget.querySelector(".target").innerHTML = res[0].target_move;
        }

        this.initial_render = false;
        this.load_data(this.initial_render);

        if (!this.state.entries) this.state.entries = [];
        this.state.entries = [ev.target.value];
    }

    async unfoldAll(ev) {
        const tbodyEl = this.tbody();
        if (!tbodyEl) return;

        if (!ev.target.classList.contains("selected-filter")) {
            for (let i = 0; i < tbodyEl.children.length; i++) {
                tbodyEl.children[i].classList.add("show");
            }
            ev.target.classList.add("selected-filter");
        } else {
            for (let i = 0; i < tbodyEl.children.length; i++) {
                tbodyEl.children[i].classList.remove("show");
            }
            ev.target.classList.remove("selected-filter");
        }
    }

    async apply_date(ev) {
        if (ev.target.name === "start_date") {
            this.filter = {
                ...this.filter,
                date_from: ev.target.value,
            };
            this.state.date_from = ev.target.value;
        } else if (ev.target.name === "end_date") {
            this.filter = {
                ...this.filter,
                date_to: ev.target.value,
            };
            this.state.date_to = ev.target.value;
        } else {
            const dataVal = ev.target.getAttribute("data-value");
            if (dataVal) {
                this.filter = dataVal;
                this.state.date_range = dataVal;
            }
        }

        await this.orm.call("dynamic.balance.sheet.report", "filter", [
            this.wizard_id,
            this.filter,
        ]);
        this.initial_render = false;
        this.load_data(this.initial_render);
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
        const monthNamesShort = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ];
        let res = await this.orm.call("dynamic.balance.sheet.report", "comparison_filter", [
            this.wizard_id,
            this.state.comparison,
        ]);
        this.state.year = [monthNamesShort[now.getMonth()] + "  " + now.getFullYear()];
        for (let length = 0; length < res.length; length++) {
            const dateObject = new Date(res[length]["date_to"]);
            this.state.year.push(
                monthNamesShort[dateObject.getMonth()] + "  " + dateObject.getFullYear()
            );
        }
        this.load_data(this.initial_render);
    }

    sumGrossProfit(op_inc, cor) {
        const stringValue = cor || "0";
        const floatValue = parseFloat(String(stringValue).replace(/,/g, "")) || 0;
        return (parseFloat(op_inc) || 0) + floatValue;
    }

    async applyComparisonYear() {
        const periodYearEl = this.period_year();
        if (!periodYearEl) return;

        this.state.comparison = periodYearEl.value;
        this.state.comparison_type = "year";
        let res = await this.orm.call(
            "dynamic.balance.sheet.report",
            "comparison_filter_year",
            [this.wizard_id, this.state.comparison]
        );
        this.state.year = [now.getFullYear()];
        for (let length = 0; length < res.length; length++) {
            const dateObject = new Date(res[length]["date_to"]);
            this.state.year.push(dateObject.getFullYear());
        }
        this.load_data(this.initial_render);
    }

    apply_comparison() {
        this.state.comparison = false;
        this.state.comparison_type = null;
        this.state.year = [now.getFullYear()];
    }
}

actionRegistry.add("dfr_n", ProfitAndLoss);
