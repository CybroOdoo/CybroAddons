import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { getCurrency } from "@web/core/currency";
import { deserializeDate, formatDate } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { Notebook } from "@web/core/notebook/notebook";
import { RecordSelector } from "@web/core/record_selectors/record_selector";
import { Record } from "@web/model/record";
import { Field } from "@web/views/fields/field";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { formatMonetary } from "@web/views/fields/formatters";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

const MODEL = "account.bank.statement.line";
const ITEMS = "account.move.line";
const VIEW_KEY = "base_accounting_kit.bank_rec_view";

function savedView() {
    try {
        return browser.localStorage.getItem(VIEW_KEY) === "list" ? "list" : "cards";
    } catch {
        return "cards";
    }
}

/**
 * Reconciliation screen of the kit: the transactions of a journal grouped
 * by what to do next (sure match / please confirm / needs you), and a
 * drawer to match the selected one with suggestions, any open item,
 * accounts or a model, with a preview of the entry. The server (statement
 * line kit_rec_* methods, on the matching engine) proposes and books
 * everything.
 */
export class BankReconciliation extends Component {
    static template = "base_accounting_kit.BankReconciliation";
    static components = { ControlPanel, Dropdown, DropdownItem, Notebook, RecordSelector, Record, Field };

    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.ui = useService("ui");
        this.groups = [
            { key: "sure", label: _t("Sure match"), hint: _t("safe to accept in one click"), badge: "success", status: _t("Sure match") },
            { key: "confirm", label: _t("Please confirm"), hint: _t("a likely match was found"), badge: "warning", status: _t("Suggestion") },
            { key: "needs", label: _t("Needs you"), hint: _t("nothing was found"), badge: "danger", status: _t("To do") },
            { key: "check", label: _t("To check"), hint: _t("booked, waiting for a review"), badge: "info", status: _t("To check") },
            { key: "done", label: _t("Reconciled"), hint: "", badge: "secondary", status: _t("Reconciled") },
        ];
        this.statuses = [
            ["todo", _t("To reconcile")],
            ["check", _t("To check")],
            ["done", _t("Reconciled")],
            ["all", _t("All")],
        ];
        this.writeoffRecordProps = {
            resModel: MODEL,
            mode: "edit",
            fieldNames: ["account_id", "tax_ids", "analytic_distribution", "label", "amount"],
            fields: {
                account_id: { name: "account_id", type: "many2one", relation: "account.account", string: _t("Account") },
                tax_ids: { name: "tax_ids", type: "many2many", relation: "account.tax", string: _t("Taxes") },
                analytic_distribution: { name: "analytic_distribution", type: "json", string: _t("Analytic") },
                label: { name: "label", type: "char", string: _t("Label") },
                amount: { name: "amount", type: "float", string: _t("Amount") },
            },
            values: {},
            hooks: { onRootLoaded: (record) => (this.writeoffRecord = record) },
        };
        this.state = proxy({
            data: null, folded: {}, line: null, selected: {}, extraItems: {}, gap: "open", modelId: false,
            partnerId: false, writeoffs: [], writeoffKey: 1, preview: null, search: "",
            searchText: "", searchResult: null, busy: false, view: savedView(),
            mode: this.props.action.params?.mode === "open" ? "open" : "bank", journalId: false, date: "",
        });
        this.labels = { chooseFirst: _t("Choose an item, an account or a model first") };
        this.accountTypes = [
            ["receivable", _t("Receivable")],
            ["payable", _t("Payable")],
            ["other", _t("Other reconcilable accounts")],
        ];
        this.previewSequence = 0;
        this.lineSequence = 0;
        useHotkey("escape", () => this.closeLine(), { bypassEditableProtection: true });
        useHotkey("j", () => this.moveSelection(1));
        useHotkey("k", () => this.moveSelection(-1));
        useHotkey("enter", () => this.state.line && !this.state.line.row.reconciled && this.canValidate() && this.validate());
        onWillStart(async () => {
            const params = this.props.action.params || {};
            if (this.state.mode === "open") {
                await this.load({ account_type: params.account_type, partner_id: params.partner_id });
                // Opened from the journal items list: those items ticked.
                const row = params.account_id && this.state.data.rows.find(
                    (r) => r.partner_id === params.partner_id && r.account_id === params.account_id);
                if (row) {
                    await this.openLine(row);
                    if (params.selected) {
                        this.state.selected = Object.fromEntries(params.selected.map((id) => [id, true]));
                        this.refreshPreview();
                    }
                }
            } else {
                await this.load({ journal_id: params.journal_id, status: "todo" });
            }
        });
    }

    // Data -----------------------------------------------------------------
    isOpen() {
        return this.state.mode === "open";
    }

    async load(filters) {
        const data = this.isOpen()
            ? await this.orm.call(ITEMS, "kit_open_load", [filters])
            : await this.orm.call(MODEL, "kit_rec_load", [filters]);
        this.state.data = data;
        this.state.search = data.filters.search;
        this.env.config.setDisplayName(this.isOpen()
            ? _t("Reconcile · Open items (%s)", this.accountTypeLabel())
            : _t("Reconcile · %s", data.journal.name || _t("no bank journal")));
    }

    setMode(mode) {
        if (mode === this.state.mode) {
            return;
        }
        this.closeLine();
        this.state.mode = mode;
        this.state.folded = {};
        return this.load(mode === "open" ? {} : { status: "todo" });
    }

    accountTypeLabel() {
        const type = this.state.data?.filters.account_type || "receivable";
        return this.accountTypes.find((t) => t[0] === type)[1];
    }

    openItemsList() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: _t("Open items"),
            res_model: ITEMS,
            views: [[false, "list"], [false, "form"]],
            domain: [["reconciled", "=", false], ["account_id.reconcile", "=", true], ["parent_state", "=", "posted"]],
            context: { search_default_group_by_partner: 1 },
        });
    }

    reload(changes = {}) {
        return this.load({ ...this.state.data.filters, ...changes });
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            this.reload({ search: ev.target.value });
        }
    }

    statusLabel() {
        return this.statuses.find((s) => s[0] === this.state.data.filters.status)[1];
    }

    rowsOf(key) {
        return this.state.data.rows.filter((row) => row.group === key);
    }

    visibleGroups() {
        return this.groups.filter((group) => this.rowsOf(group.key).length);
    }

    visibleRows() {
        return this.visibleGroups().flatMap((group) => (this.state.folded[group.key] ? [] : this.rowsOf(group.key)));
    }

    setView(view) {
        this.state.view = view;
        try {
            browser.localStorage.setItem(VIEW_KEY, view);
        } catch {
            // Not saved (private window): the choice lasts for this screen only.
        }
    }

    showCards() {
        // Phones and narrow windows always get cards (a table does not fit).
        return this.state.view === "cards" || !!this.ui.isSmall;
    }

    proposalTitle(row) {
        return [row.proposal, ...row.reasons].filter(Boolean).join(" · ");
    }

    proposalText(row) {
        return [row.proposal, row.reasons[0]].filter(Boolean).join(" · ");
    }

    toggleGroup(key) {
        this.state.folded[key] = !this.state.folded[key];
    }

    date(value) {
        return value ? formatDate(deserializeDate(value)) : "";
    }

    money(value, currencyId) {
        return formatMonetary(value, { currencyId: currencyId || this.state.data.currency_id || this.state.data.journal?.currency_id });
    }

    amountInput(value) {
        const digits = getCurrency(this.state.line.currency_id)?.digits?.[1] ?? 2;
        return Number(value).toFixed(digits);
    }

    newTransaction() {
        this.actionService.doAction("base_accounting_kit.action_bank_statement_line_form_bank_reconcile_widget", {
            additionalContext: { default_journal_id: this.state.data.journal.id },
            onClose: () => this.reload(),
        });
    }

    openList() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: _t("Transactions"),
            res_model: MODEL,
            views: [[false, "list"], [false, "form"]],
            domain: [["journal_id", "=", this.state.data.journal.id]],
            context: { default_journal_id: this.state.data.journal.id },
        });
    }

    // Drawer ---------------------------------------------------------------
    async openLine(row, partnerId = null) {
        // Only the last opened transaction fills the drawer (fast clicks, J/K).
        const sequence = ++this.lineSequence;
        if (this.isOpen()) {
            const line = await this.orm.call(ITEMS, "kit_open_partner", [row.partner_id, row.account_id]);
            if (sequence !== this.lineSequence) {
                return;
            }
            Object.assign(this.state, {
                line, selected: Object.fromEntries(line.selected.map((id) => [id, true])), extraItems: {},
                gap: line.gap, writeoffs: [], modelId: false, journalId: line.journal_id, date: line.date,
                preview: null,
            });
            this.state.writeoffKey++;
            this.refreshPreview();
            this.scrollToSelected();
            return;
        }
        const line = await this.orm.call(MODEL, "kit_rec_line", [[row.id], partnerId]);
        if (sequence !== this.lineSequence) {
            return;
        }
        Object.assign(this.state, {
            line, selected: { ...line.selected }, extraItems: {}, gap: line.gap, writeoffs: [],
            modelId: line.models.find((m) => m.matched)?.id || false, partnerId: line.partner.id || false,
            searchText: "", searchResult: null, preview: null,
        });
        this.state.writeoffKey++;
        this.refreshPreview();
        this.scrollToSelected();
    }

    scrollToSelected() {
        // Keep the open row visible in the scrolled list or cards.
        browser.requestAnimationFrame(() => {
            document.querySelector(".o_kit_bank_rec .o_kit_rec_selected")?.scrollIntoView({ block: "nearest" });
        });
    }

    closeLine() {
        this.lineSequence++;
        this.state.line = null;
    }

    moveSelection(step) {
        const rows = this.visibleRows();
        if (!rows.length) {
            return;
        }
        const index = this.state.line ? rows.findIndex((row) => row.id === this.state.line.row.id) : -1;
        const next = rows[Math.min(Math.max(index + step, 0), rows.length - 1)];
        if (next) {
            this.openLine(next);
        }
    }

    changePartner(partnerId) {
        this.openLine(this.state.line.row, partnerId || false);
    }

    isSelected(item) {
        return item.id in this.state.selected;
    }

    toggleItem(item) {
        if (this.isOpen()) {
            if (this.isSelected(item)) {
                delete this.state.selected[item.id];
            } else {
                this.state.selected[item.id] = true;
            }
            this.refreshPreview();
            return;
        }
        if (this.isSelected(item)) {
            delete this.state.selected[item.id];
        } else {
            this.state.extraItems[item.id] = item;
            this.state.selected[item.id] = Math.abs(item.residual);
        }
        this.refreshPreview();
    }

    setItemAmount(item, ev) {
        const value = parseFloat(ev.target.value);
        if (!isNaN(value)) {
            this.state.selected[item.id] = Math.min(Math.abs(value), Math.abs(item.residual));
            this.refreshPreview();
        }
    }

    selectSuggestion(suggestion) {
        this.state.selected = Object.fromEntries(suggestion.ids.map((id) => [id, true]));
        this.state.gap = suggestion.discount ? "discount" : "open";
        this.refreshPreview();
    }

    selectAll(items) {
        const all = items.every((item) => this.isSelected(item));
        for (const item of items) {
            if (all) {
                delete this.state.selected[item.id];
            } else {
                this.state.selected[item.id] = true;
            }
        }
        this.refreshPreview();
    }

    hasOpenDifference() {
        return Math.abs(this.difference(false)) >= 0.005;
    }

    setJournal(ev) {
        this.state.journalId = parseInt(ev.target.value);
        this.refreshPreview();
    }

    setDate(ev) {
        this.state.date = ev.target.value;
        this.refreshPreview();
    }

    openItems() {
        return [...this.state.line.debits, ...this.state.line.credits];
    }

    selectCombination(combination) {
        this.state.selected = {};
        for (const item of combination.items) {
            this.state.extraItems[item.id] = item;
            this.state.selected[item.id] = Math.abs(item.residual);
        }
        this.refreshPreview();
    }

    allItems() {
        if (this.isOpen()) {
            return Object.fromEntries(this.openItems().map((item) => [item.id, item]));
        }
        const items = { ...this.state.extraItems };
        for (const item of this.state.line.suggestions) {
            items[item.id] = item;
        }
        return items;
    }

    selectedItems() {
        const items = this.allItems();
        return Object.keys(this.state.selected).map((id) => items[id]).filter(Boolean);
    }

    hasSelection() {
        return Object.keys(this.state.selected).length > 0;
    }

    canDiscount() {
        return this.selectedItems().some((item) => item.discounted !== null && item.discounted !== undefined);
    }

    openSideTotal(sign) {
        return this.selectedItems().filter((item) => Math.sign(item.residual) === sign)
            .reduce((total, item) => total + item.residual, 0);
    }

    selectedTotal() {
        const items = this.allItems();
        return Object.entries(this.state.selected).reduce(
            (total, [id, value]) => total + Math.sign(items[id]?.residual || 1) * value, 0);
    }

    writeoffTotal() {
        if (this.isOpen()) {
            // Write-off lines take away the difference (same side as it).
            const sign = Math.sign(this.difference(false)) || 1;
            return this.state.writeoffs.reduce((total, w) => total + sign * (w.amount || 0), 0);
        }
        // Accounts are booked against the transaction (same side as it).
        const sign = Math.sign(this.difference(false)) || Math.sign(this.state.line.amount) || 1;
        return this.state.writeoffs.reduce((total, w) => total + sign * (w.amount || 0), 0);
    }

    difference(withWriteoffs = true) {
        if (this.isOpen()) {
            const net = this.openSideTotal(1) + this.openSideTotal(-1);
            return withWriteoffs && this.state.gap === "writeoff" ? net - this.writeoffTotal() : net;
        }
        const rest = this.state.line.amount - this.selectedTotal();
        return withWriteoffs ? rest - this.writeoffTotal() : rest;
    }

    canValidate() {
        if (this.isOpen()) {
            // Two items to match, or items and a write-off of the rest.
            const count = Object.keys(this.state.selected).length;
            const writeoff = (this.state.gap === "writeoff" && this.state.writeoffs.length > 0)
                || (this.state.gap === "model" && !!this.state.modelId) || this.state.gap === "discount";
            return count >= 2 || (count >= 1 && writeoff && Math.abs(this.difference(false)) >= 0.005);
        }
        // Something to book: an item, an account line or a chosen model.
        return this.hasSelection() || this.state.writeoffs.length > 0
            || (this.state.gap === "model" && !!this.state.modelId);
    }

    hasDifference() {
        return Math.abs(this.difference()) >= 0.005;
    }

    setGap(gap) {
        this.state.gap = gap;
        this.refreshPreview();
    }

    chooseModel(modelId) {
        this.state.modelId = modelId;
        this.state.gap = "model";
        this.refreshPreview();
    }

    modelName() {
        return this.state.line.models.find((m) => m.id === this.state.modelId)?.name || _t("Choose a model");
    }

    // Search entries ---------------------------------------------------------
    async searchEntries(ev) {
        if (ev && ev.key !== "Enter") {
            return;
        }
        this.state.searchResult = await this.orm.call(MODEL, "kit_rec_search", [[this.state.line.row.id], this.state.searchText, 0]);
    }

    // Book to account --------------------------------------------------------
    addWriteoff() {
        if (this.isOpen()) {
            this.state.gap = "writeoff";
        }
        const data = this.writeoffRecord?.data;
        if (!data?.account_id) {
            this.notification.add(_t("Choose an account."), { type: "warning" });
            return;
        }
        this.state.writeoffs.push({
            account_id: data.account_id.id,
            account_name: data.account_id.display_name,
            tax_ids: data.tax_ids.currentIds,
            tax_names: data.tax_ids.records.map((r) => r.data.display_name).join(", "),
            analytic_distribution: data.analytic_distribution || false,
            label: data.label || "",
            amount: Math.abs(data.amount) || Math.abs(this.difference()),
        });
        this.state.writeoffKey++;
        this.refreshPreview();
    }

    removeWriteoff(index) {
        this.state.writeoffs.splice(index, 1);
        this.refreshPreview();
    }

    // Preview and validation ------------------------------------------------
    selection({ partial = false, toCheck = false } = {}) {
        if (this.isOpen()) {
            const line = this.state.line;
            return {
                account_id: line.account.id, partner_id: line.partner.id,
                items: Object.keys(this.state.selected).map((id) => parseInt(id)),
                gap: this.state.gap, model_id: this.state.modelId, journal_id: this.state.journalId,
                date: this.state.date,
                writeoffs: this.state.writeoffs.map((w) => ({
                    account_id: w.account_id, tax_ids: w.tax_ids, analytic_distribution: w.analytic_distribution,
                    label: w.label, amount: w.amount,
                })),
            };
        }
        return {
            items: Object.entries(this.state.selected).map(([id, value]) => [parseInt(id), value]),
            writeoffs: this.state.writeoffs.map((w) => ({
                account_id: w.account_id, tax_ids: w.tax_ids, analytic_distribution: w.analytic_distribution,
                label: w.label, amount: w.amount,
            })),
            gap: partial ? "suspense" : this.state.gap,
            model_id: this.state.modelId,
            partner_id: this.state.partnerId,
            to_check: toCheck,
        };
    }

    async refreshPreview() {
        const line = this.state.line;
        if (!line || line.row.reconciled || line.row.to_check) {
            return;
        }
        const sequence = ++this.previewSequence;
        const preview = this.isOpen()
            ? await this.orm.call(ITEMS, "kit_open_preview", [this.selection()])
            : await this.orm.call(MODEL, "kit_rec_preview", [[line.row.id], this.selection()]);
        if (sequence === this.previewSequence) {
            this.state.preview = preview;
        }
    }

    async validate({ partial = false, toCheck = false } = {}) {
        const line = this.state.line;
        if (this.state.busy || !this.canValidate()) {
            return;
        }
        const rows = this.visibleRows();
        const next = rows[rows.findIndex((row) => row.id === line.row.id) + 1];
        this.state.busy = true;
        try {
            if (this.isOpen()) {
                await this.orm.call(ITEMS, "kit_open_validate", [this.selection()]);
            } else {
                await this.orm.call(MODEL, "kit_rec_validate", [[line.row.id], this.selection({ partial, toCheck })]);
            }
        } finally {
            this.state.busy = false;
        }
        this.notification.add(_t("%s reconciled.", line.row.label || _t("Transaction")), { type: "success" });
        await this.reload();
        if (next && this.state.data.rows.some((row) => row.id === next.id)) {
            await this.openLine(next);
        } else {
            this.closeLine();
        }
    }

    async setToCheck(row, toCheck) {
        await this.orm.call(MODEL, "kit_rec_set_check", [[row.id], toCheck]);
        await this.reload();
        this.closeLine();
    }

    async undo(row) {
        await this.orm.call(MODEL, "kit_rec_undo", [[row.id]]);
        await this.reload();
        this.closeLine();
    }

    async acceptSure() {
        const ids = this.rowsOf("sure").map((row) => row.id);
        const count = this.isOpen()
            ? await this.orm.call(ITEMS, "kit_open_accept_sure", [ids])
            : await this.orm.call(MODEL, "kit_rec_accept_sure", [ids]);
        this.notification.add(this.isOpen() ? _t("%s matches made.", count) : _t("%s transactions reconciled.", count),
                              { type: "success" });
        this.closeLine();
        await this.reload();
    }

    openEntry(row) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "account.move",
            res_id: row.move_id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("kit_bank_reconciliation", BankReconciliation);
