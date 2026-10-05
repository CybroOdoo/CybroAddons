import { Domain } from "@web/core/domain";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { MultiRecordSelector } from "@web/core/record_selectors/multi_record_selector";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy, t, useProps } from "@odoo/owl";

const { DateTime } = luxon;

export const PERIODS = [
    { value: "all", label: _t("All time") },
    { value: "today", label: _t("Today") },
    { value: "this_week", label: _t("This week") },
    { value: "this_month", label: _t("This month") },
    { value: "this_quarter", label: _t("This quarter") },
    { value: "this_year", label: _t("This year") },
    { value: "last_7_days", label: _t("Last 7 days") },
    { value: "last_30_days", label: _t("Last 30 days") },
    { value: "last_12_months", label: _t("Last 12 months") },
    { value: "custom", label: _t("Custom range") },
];
const PREFERRED_DATE_FIELDS = ["date_order", "date", "invoice_date", "date_deadline", "create_date"];
const CONDITION_TYPES = ["selection", "boolean", "many2one", "char"];
const PREFERRED_CONDITIONS = ["state", "stage_id", "user_id", "team_id", "partner_id", "company_id", "categ_id"];

/**
 * Filters chosen by the viewer of a block. They are not part of the dashboard: each
 * viewer narrows the blocks for themselves.
 *
 * - dateField / dateFieldType / period / from / to: restrict to a period
 * - values: [{ label, domain }] of the block's groups to keep
 * - conditions: [{ field, type, label, values }] on other fields of the model
 */
export function emptyFilter() {
    return { dateField: false, dateFieldType: false, period: "all", from: "", to: "", values: [], conditions: [] };
}

function isConditionSet(condition) {
    return condition.type === "boolean" ? condition.values.length === 1 : condition.values.length > 0;
}

export function countActiveFilters(filter) {
    if (!filter) {
        return 0;
    }
    const hasPeriod = filter.dateField && filter.period !== "all" && (filter.period !== "custom" || filter.from || filter.to);
    return (hasPeriod ? 1 : 0) + (filter.values.length ? 1 : 0) + filter.conditions.filter(isConditionSet).length;
}

/**
 * @returns {[DateTime|null, DateTime|null]} start (included) and end (excluded)
 */
export function getPeriodRange(period, from, to) {
    const now = DateTime.local();
    const today = now.startOf("day");
    switch (period) {
        case "today":
            return [today, today.plus({ days: 1 })];
        case "this_week":
            return [now.startOf("week"), now.startOf("week").plus({ weeks: 1 })];
        case "this_month":
            return [now.startOf("month"), now.startOf("month").plus({ months: 1 })];
        case "this_quarter":
            return [now.startOf("quarter"), now.startOf("quarter").plus({ quarters: 1 })];
        case "this_year":
            return [now.startOf("year"), now.startOf("year").plus({ years: 1 })];
        case "last_7_days":
            return [today.minus({ days: 6 }), today.plus({ days: 1 })];
        case "last_30_days":
            return [today.minus({ days: 29 }), today.plus({ days: 1 })];
        case "last_12_months":
            return [now.startOf("month").minus({ months: 11 }), now.startOf("month").plus({ months: 1 })];
        case "custom":
            return [
                from ? DateTime.fromISO(from).startOf("day") : null,
                to ? DateTime.fromISO(to).startOf("day").plus({ days: 1 }) : null,
            ];
        default:
            return [null, null];
    }
}

/**
 * Domain of the records kept by the filter of a block.
 *
 * @returns {Array} a domain in list form, empty when nothing is filtered
 */
export function buildFilterDomain(filter) {
    if (!countActiveFilters(filter)) {
        return [];
    }
    const domains = [];
    if (filter.dateField && filter.period !== "all") {
        const [start, end] = getPeriodRange(filter.period, filter.from, filter.to);
        const serialize = filter.dateFieldType === "datetime" ? serializeDateTime : serializeDate;
        if (start) {
            domains.push(new Domain([[filter.dateField, ">=", serialize(start)]]));
        }
        if (end) {
            domains.push(new Domain([[filter.dateField, "<", serialize(end)]]));
        }
    }
    if (filter.values.length) {
        domains.push(Domain.or(filter.values.map((value) => new Domain(value.domain))));
    }
    for (const condition of filter.conditions.filter(isConditionSet)) {
        if (condition.type === "boolean") {
            domains.push(new Domain([[condition.field, "=", condition.values[0]]]));
        } else if (condition.type === "char") {
            domains.push(Domain.or(condition.values.map((value) => new Domain([[condition.field, "ilike", value]]))));
        } else {
            domains.push(new Domain([[condition.field, "in", condition.values]]));
        }
    }
    return Domain.and(domains).toList();
}

/**
 * Short description of the active filters, shown on the block (and in its PDF).
 */
export function getFilterSummary(filter) {
    if (!countActiveFilters(filter)) {
        return "";
    }
    const parts = [];
    if (filter.dateField && filter.period !== "all") {
        if (filter.period === "custom") {
            parts.push([filter.from, filter.to].filter(Boolean).join(" → "));
        } else {
            parts.push(PERIODS.find((period) => period.value === filter.period).label);
        }
    }
    if (filter.values.length) {
        parts.push(filter.values.map((value) => value.label).join(", "));
    }
    for (const condition of filter.conditions.filter(isConditionSet)) {
        if (condition.type === "boolean") {
            parts.push(`${condition.label}: ${condition.values[0] ? _t("Yes") : _t("No")}`);
        } else {
            parts.push(`${condition.label}: ${(condition.valueLabels || condition.values).join(", ")}`);
        }
    }
    return parts.join(" · ");
}

/**
 * Side panel where the viewer filters one block of a dashboard, with options
 * matching the data of the block: a period on its date fields, the values it is
 * grouped by, and conditions on its other fields.
 */
export class BlockFilterPanel extends Component {
    static template = "odoo_dynamic_dashboard.BlockFilterPanel";
    static components = { MultiRecordSelector };
    props = useProps({
        block: t.object(),
        filter: t.object(),
        // called with the changed keys of the filter
        onChange: t.function(),
        onClose: t.function(),
    });

    periods = PERIODS;

    setup() {
        this.fieldService = useService("field");
        this.orm = useService("orm");
        this.state = proxy({ fields: [] });
        onWillStart(async () => {
            const fields = await this.fieldService.loadFields(this.props.block.model);
            this.state.fields = Object.entries(fields)
                .map(([name, field]) => ({ ...field, name }))
                .sort((field1, field2) => field1.string.localeCompare(field2.string));
            if (!this.getFilter().dateField && this.getDateFields().length) {
                const dateField = this.getDateFields()[0];
                this.update({ dateField: dateField.name, dateFieldType: dateField.type });
            }
        });
    }

    getDateFields() {
        const { group_by: groupBy } = this.props.block;
        const fields = this.state.fields.filter((field) => field.store && ["date", "datetime"].includes(field.type));
        const rank = (field) => {
            if (field.name === groupBy) {
                return -1; // a block grouped by a date is filtered on that date
            }
            const index = PREFERRED_DATE_FIELDS.indexOf(field.name);
            return index === -1 ? PREFERRED_DATE_FIELDS.length : index;
        };
        return [...fields].sort((field1, field2) => rank(field1) - rank(field2));
    }

    getValueOptions() {
        return this.props.block.filterOptions || [];
    }

    isValueSelected(option) {
        return this.getFilter().values.some((value) => value.label === option.label);
    }

    getConditionFields() {
        const used = new Set(this.getFilter().conditions.map((condition) => condition.field));
        const fields = this.state.fields.filter(
            (field) => field.store && CONDITION_TYPES.includes(field.type) && !used.has(field.name)
        );
        const rank = (field) => {
            const index = PREFERRED_CONDITIONS.indexOf(field.name);
            return index === -1 ? PREFERRED_CONDITIONS.length : index;
        };
        return [...fields].sort((field1, field2) => rank(field1) - rank(field2));
    }

    getField(fieldName) {
        return this.state.fields.find((field) => field.name === fieldName);
    }

    /**
     * The current filter of the block. Read from the block rather than from the props,
     * which are only updated at the next render: two quick changes must both apply.
     */
    getFilter() {
        return this.props.block.filter || this.props.filter;
    }

    update(changes) {
        this.props.onChange(changes);
    }

    onDateFieldChange(ev) {
        const field = this.getField(ev.target.value);
        this.update({ dateField: field.name, dateFieldType: field.type });
    }

    onPeriodChange(period) {
        this.update({ period });
    }

    onCustomDateChange(key, ev) {
        this.update({ [key]: ev.target.value, period: "custom" });
    }

    toggleValue(option) {
        const values = this.isValueSelected(option)
            ? this.getFilter().values.filter((value) => value.label !== option.label)
            : [...this.getFilter().values, { label: option.label, domain: option.domain }];
        this.update({ values });
    }

    addCondition(ev) {
        const field = this.getField(ev.target.value);
        ev.target.value = "";
        if (field) {
            const condition = { field: field.name, type: field.type, label: field.string, values: [], valueLabels: [] };
            this.update({ conditions: [...this.getFilter().conditions, condition] });
        }
    }

    removeCondition(condition) {
        this.update({ conditions: this.getFilter().conditions.filter((item) => item.field !== condition.field) });
    }

    updateCondition(condition, values, valueLabels = values) {
        const conditions = this.getFilter().conditions.map((item) =>
            item.field === condition.field ? { ...item, values, valueLabels } : item
        );
        this.update({ conditions });
    }

    toggleSelectionValue(condition, value) {
        const values = condition.values.includes(value)
            ? condition.values.filter((item) => item !== value)
            : [...condition.values, value];
        const selection = this.getField(condition.field)?.selection || [];
        const labels = values.map((item) => selection.find(([key]) => key === item)?.[1] || item);
        this.updateCondition(condition, values, labels);
    }

    onBooleanChange(condition, ev) {
        const value = ev.target.value;
        this.updateCondition(condition, value === "" ? [] : [value === "1"]);
    }

    onCharInput(condition, ev) {
        const value = ev.target.value.trim();
        this.updateCondition(condition, value ? [value] : []);
    }

    async onRecordsUpdate(condition, resIds) {
        // the summary on the block shows the names of the records
        const { relation } = this.getField(condition.field);
        const records = resIds.length ? await this.orm.read(relation, resIds, ["display_name"]) : [];
        const names = resIds.map((id) => records.find((record) => record.id === id)?.display_name || String(id));
        this.updateCondition(condition, resIds, names);
    }

    clear() {
        const { dateField, dateFieldType } = this.getFilter();
        this.props.onChange({ ...emptyFilter(), dateField, dateFieldType });
    }
}
