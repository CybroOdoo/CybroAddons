import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { MultiRecordSelector } from "@web/core/record_selectors/multi_record_selector";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { formatMonetary } from "@web/views/fields/formatters";
import { formatFloat } from "@web/core/utils/numbers";
import { getCurrency } from "@web/core/currency";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

/**
 * Screen shared by every dynamic report of the kit. The report model
 * (action params `model`) computes everything on the server: this component
 * only keeps the options, shows the lines and asks for unfolds, drill-downs
 * and exports.
 */
export class DynamicReport extends Component {
    static template = "base_accounting_kit.DynamicReport";
    static components = { ControlPanel, Dropdown, DropdownItem, MultiRecordSelector };

    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.model = this.props.action.params?.model;
        this.datePresets = [
            ["this_month", _t("This Month")],
            ["this_quarter", _t("This Quarter")],
            ["this_year", _t("This Financial Year")],
            ["last_month", _t("Last Month")],
            ["last_quarter", _t("Last Quarter")],
            ["last_year", _t("Last Financial Year")],
        ];
        this.singleDatePresets = [
            ["today", _t("Today")],
            ["last_month", _t("End of Last Month")],
            ["last_quarter", _t("End of Last Quarter")],
            ["last_year", _t("End of Last Financial Year")],
        ];
        this.labels = { unfold: _t("Unfold all"), fold: _t("Fold all") };
        this.amountUnits = {
            full: {},
            int: { digits: [69, 0] },
            k: { divisor: 1000, suffix: "K" },
            m: { divisor: 1000000, suffix: "M" },
        };
        this.state = proxy({
            report: null, customFrom: "", customTo: "", periods: 1,
            savedFilters: [], filterName: "", filterDefault: false,
        });
        onWillStart(async () => {
            this.state.savedFilters = await this.orm.call(this.model, "get_saved_filters", [this.props.action.id]);
            const saved = this.state.savedFilters.find((f) => f.is_default);
            // options sent by a drill-down (e.g. P&L account -> General Ledger)
            // win over the saved default filter
            const params = this.props.action.params?.options || {};
            await this.load(params.account_ids?.length ? { ...(saved?.options || {}), ...params }
                : { ...params, ...(saved?.options || {}) });
        });
    }

    get report() {
        return this.state.report;
    }

    get options() {
        return this.state.report.options;
    }

    async load(options) {
        this.state.report = await this.orm.call(this.model, "get_report", [options]);
        // The breadcrumb names the report shown (e.g. after Options > Report).
        this.env.config.setDisplayName(this.state.report.title);
    }

    reload(changes) {
        return this.load({ ...this.options, ...changes });
    }

    // Filters ------------------------------------------------------------
    hasFilter(name) {
        return this.report.filters.includes(name);
    }

    get presets() {
        return this.report.date_mode === "single" ? this.singleDatePresets : this.datePresets;
    }

    get dateLabel() {
        const preset = this.presets.find((p) => p[0] === this.options.date_preset);
        if (preset) {
            return preset[1];
        }
        return this.options.date_from
            ? `${this.options.date_from} - ${this.options.date_to}`
            : this.options.date_to;
    }

    comparisonLabel() {
        if (this.options.columns_by) {
            return this.options.columns_by === "quarter" ? _t("By quarter") : _t("By month");
        }
        const { periods, type } = this.options.comparison;
        if (!periods) {
            return _t("None");
        }
        return type === "last_year" ? _t("Last year (%s)", periods) : _t("Previous (%s)", periods);
    }

    journalsLabel() {
        const ids = this.options.journal_ids;
        if (!ids.length) {
            return _t("All");
        }
        const codes = this.report.journals.filter((j) => ids.includes(j.id)).map((j) => j.code);
        return codes.length <= 2 ? codes.join(", ") : _t("%s selected", codes.length);
    }

    countLabel(ids) {
        return ids.length ? _t("%s selected", ids.length) : _t("All");
    }

    recordFilters() {
        // partner / analytic / account filters of the report, shown as chips
        return [
            { key: "partner_ids", filter: "partners", model: "res.partner", label: _t("Partners"), icon: "account_circle", domain: [] },
            { key: "analytic_ids", filter: "analytic", model: "account.analytic.account", label: _t("Analytic"), icon: "account_tree", domain: [] },
            { key: "account_ids", filter: "accounts", model: "account.account", label: _t("Accounts"), icon: "account_tree", domain: this.report.account_domain },
        ].filter((flt) => this.hasFilter(flt.filter));
    }

    isUnfolded() {
        return this.options.unfold_all || this.options.unfolded.length > 0;
    }

    setOption(definition, value) {
        if (definition.type === "number") {
            value = parseInt(value) || definition.default;
        }
        return this.reload({ [definition.key]: value });
    }

    applyCustomDates() {
        return this.reload({
            date_preset: "custom",
            date_from: this.state.customFrom || this.options.date_from,
            date_to: this.state.customTo || this.options.date_to,
        });
    }

    toggleJournal(journalId) {
        const ids = new Set(this.options.journal_ids);
        ids.has(journalId) ? ids.delete(journalId) : ids.add(journalId);
        return this.reload({ journal_ids: [...ids] });
    }

    setComparison(periods, type) {
        return this.reload({
            comparison: { periods, type: type || this.options.comparison.type },
            columns_by: "",
        });
    }

    setColumnsBy(columnsBy) {
        // one column per month / quarter (RI 3.2); replaces the comparison
        return this.reload({ columns_by: columnsBy, comparison: { ...this.options.comparison, periods: 0 } });
    }

    onSearch(ev) {
        if (ev.key === "Enter") {
            this.reload({ search: ev.target.value });
        }
    }

    // Saved filters (ir.filters of the user, per report menu) -----------
    async saveFilter() {
        this.state.savedFilters = await this.orm.call(this.model, "action_save_filter", [
            this.options, this.state.filterName, this.props.action.id, this.state.filterDefault,
        ]);
        Object.assign(this.state, { filterName: "", filterDefault: false });
    }

    applyFilter(saved) {
        return this.load({ ...(this.props.action.params?.options || {}), ...saved.options });
    }

    async deleteFilter(saved) {
        await this.orm.unlink("ir.filters", [saved.id]);
        this.state.savedFilters = this.state.savedFilters.filter((f) => f.id !== saved.id);
    }

    // Lines --------------------------------------------------------------
    async toggleLine(line) {
        const lines = this.report.lines;
        if (line.unfolded) {
            this.report.lines = lines.filter((l) => l.parent_id !== line.id);
            line.unfolded = false;
            const unfolded = this.options.unfold_all
                ? lines.filter((l) => l.unfolded && l.id !== line.id).map((l) => l.id)
                : this.options.unfolded.filter((id) => id !== line.id);
            Object.assign(this.options, { unfold_all: false, unfolded });
            return;
        }
        const children = await this.orm.call(this.model, "get_lines", [this.options, line.id]);
        const index = lines.indexOf(line);
        this.report.lines = [...lines.slice(0, index + 1), ...children, ...lines.slice(index + 1)];
        line.unfolded = true;
        this.options.unfolded = [...this.options.unfolded, line.id];
    }

    unfoldAll(unfold) {
        return this.reload({ unfold_all: unfold, unfolded: [] });
    }

    formatAmount(value) {
        // amount unit (as is, without decimals, K, M); the symbol only with
        // "Currency symbol in amounts"
        const unit = this.amountUnits[this.options.amount_unit] || this.amountUnits.full;
        const noSymbol = !this.options.currency_symbol;
        if (!unit.divisor) {
            return formatMonetary(value, { currencyId: this.report.currency_id, noSymbol, digits: unit.digits });
        }
        const text = formatFloat(value / unit.divisor, { digits: [69, 1] }) + unit.suffix;
        const currency = getCurrency(this.report.currency_id);
        if (noSymbol || !currency?.symbol) {
            return text;
        }
        return currency.position === "after" ? `${text}\u00a0${currency.symbol}` : `${currency.symbol}\u00a0${text}`;
    }

    amountUnitLabel(key) {
        const code = this.report.currency_name;
        return {
            full: _t("In %s", code),
            int: _t("In %s, without decimals", code),
            k: _t("In K %s", code),
            m: _t("In M %s", code),
        }[key];
    }

    hasAmounts() {
        return this.report.columns.some((col) => col.type === "monetary");
    }

    lineClass(line) {
        // total / main / section rows, the report line style, detail rows
        return [
            line.class && `o_kit_dr_${line.class}`,
            line.style && `o_kit_dr_style_${line.style}`,
            line.parent_id && "o_kit_dr_child",
            (line.unfoldable || this.isClickable(line)) && "o_kit_dr_clickable",
        ].filter(Boolean).join(" ");
    }

    onKitLineClick(line, ev) {
        // the whole row unfolds / folds, or opens the line; selecting text
        // (to copy an amount) does nothing
        if (ev.target.closest("a") || window.getSelection()?.toString()) {
            return;
        }
        // an amount under a period column opens that period
        const cell = ev.target.closest("td");
        const column = cell && cell.cellIndex > 0 ? this.report.columns[cell.cellIndex - 1] : null;
        if (column?.date_from && this.isClickable(line)) {
            return this.openLine(line, column);
        }
        if (line.unfoldable) {
            return this.toggleLine(line);
        }
        if (this.isClickable(line)) {
            return this.openLine(line);
        }
    }

    isClickable(line) {
        // lines that open something: accounts, journal items, partners, taxes
        return ["account_", "aml_", "partner_", "tax_", "payment_"].some((prefix) => line.id.startsWith(prefix));
    }

    async openLine(line, column) {
        // an amount of a period column opens that period only (RI 3.2)
        const options = column?.date_from
            ? { ...this.options, date_preset: "custom", date_from: column.date_from,
                date_to: column.date_to, columns_by: "" }
            : this.options;
        const action = await this.orm.call(this.model, "action_open_line", [options, line.id], {
            context: { kit_period_cell: Boolean(column?.date_from) },
        });
        if (action) {
            await this.actionService.doAction(action);
        }
    }

    formatValue(value, column) {
        if (column?.type === "monetary" && typeof value === "number") {
            return this.formatAmount(value);
        }
        return value ?? "";
    }

    // Exports (recomputed on the server from the options) ------------------
    async exportPdf() {
        const action = await this.orm.call(this.model, "action_export_pdf", [this.options]);
        await this.actionService.doAction(action);
    }

    async exportCsv() {
        const action = await this.orm.call(this.model, "action_export_csv", [this.options]);
        await this.actionService.doAction(action);
    }

    printReport() {
        // the browser's print dialog with the report's print layout
        window.print();
    }

    async exportXlsx() {
        const action = await this.orm.call(this.model, "action_export_xlsx", [this.options]);
        await this.actionService.doAction(action);
    }
}

registry.category("actions").add("kit_dynamic_report", DynamicReport);
