import { DomainSelectorDialog } from "@web/core/domain_selector_dialog/domain_selector_dialog";
import { _t } from "@web/core/l10n/translation";
import { ModelSelector } from "@web/core/model_selector/model_selector";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy, t, useProps } from "@odoo/owl";
import {
    BLOCK_CATEGORIES,
    BLOCK_COLORS,
    BLOCK_ICONS,
    BLOCK_TYPES,
    BLOCK_TYPES_BY_NAME,
    BLOCK_WIDTHS,
} from "../block_catalog/block_catalog";

const NUMERIC_TYPES = ["integer", "float", "monetary"];
const GROUPABLE_TYPES = ["many2one", "selection", "char", "boolean", "date", "datetime", "integer"];
const TEMPORAL_TYPES = ["date", "datetime"];
// fields usually worth grouping by, tried in this order before any other field
const PREFERRED_GROUP_BYS = [
    "stage_id", "state", "user_id", "team_id", "partner_id", "categ_id", "product_id",
    "country_id", "type", "company_id",
];
const PREFERRED_DATE_GROUP_BYS = ["date_order", "date", "invoice_date", "date_deadline", "create_date"];
const UNLISTABLE_TYPES = ["one2many", "many2many", "binary", "html", "json", "properties", "properties_definition"];

export const AGGREGATES = [
    { value: "count", label: _t("Number of records") },
    { value: "sum", label: _t("Sum of") },
    { value: "avg", label: _t("Average of") },
    { value: "min", label: _t("Minimum of") },
    { value: "max", label: _t("Maximum of") },
];

export const DATE_GRANULARITIES = [
    { value: "day", label: _t("Day") },
    { value: "week", label: _t("Week") },
    { value: "month", label: _t("Month") },
    { value: "quarter", label: _t("Quarter") },
    { value: "year", label: _t("Year") },
];

export const VIEW_MODES = [
    { value: "list", label: _t("List") },
    { value: "kanban", label: _t("Kanban") },
    { value: "graph", label: _t("Graph") },
    { value: "pivot", label: _t("Pivot") },
];

/**
 * Side panel of the dashboard builder editing the selected block. Every change is
 * reported with ``onUpdate`` so that the dashboard refreshes the block preview.
 */
export class BlockConfigurator extends Component {
    static template = "odoo_dynamic_dashboard.BlockConfigurator";
    static components = { ModelSelector };
    props = useProps({
        block: t.object(),
        onUpdate: t.function(),
        onDuplicate: t.function(),
        onDelete: t.function(),
        onClose: t.function(),
    });

    aggregates = AGGREGATES;
    modelPlaceholder = _t("Search: Sales Order, Contact, Invoice...");
    blockColors = BLOCK_COLORS;
    blockIcons = BLOCK_ICONS;
    blockWidths = BLOCK_WIDTHS;
    dateGranularities = DATE_GRANULARITIES;
    viewModes = VIEW_MODES;

    setup() {
        this.fieldService = useService("field");
        this.dialogService = useService("dialog");
        this.state = proxy({ fields: [] });
        onWillStart(() => this.loadFields(this.props.block.model));
    }

    async loadFields(model) {
        if (!model) {
            this.state.fields = [];
            return;
        }
        const fields = await this.fieldService.loadFields(model);
        this.state.fields = Object.entries(fields)
            .map(([name, field]) => ({ ...field, name }))
            .filter((field) => field.name !== "id")
            .sort((field1, field2) => field1.string.localeCompare(field2.string));
    }

    getInfo() {
        return BLOCK_TYPES_BY_NAME[this.props.block.block_type];
    }

    getBlockTypeGroups() {
        return BLOCK_CATEGORIES.map((category) => ({
            ...category,
            blockTypes: BLOCK_TYPES.filter((info) => info.category === category.id),
        }));
    }

    getMeasureFields() {
        return this.state.fields.filter((field) => field.store && NUMERIC_TYPES.includes(field.type));
    }

    getGroupByFields() {
        const fields = this.state.fields.filter(
            (field) => field.store && field.groupable !== false && GROUPABLE_TYPES.includes(field.type)
        );
        if (this.getInfo().dateFirst) {
            // charts following a trend are usually grouped by date
            return [
                ...fields.filter((field) => TEMPORAL_TYPES.includes(field.type)),
                ...fields.filter((field) => !TEMPORAL_TYPES.includes(field.type)),
            ];
        }
        return fields;
    }

    /**
     * Pick a meaningful field to group by: dates for trend charts, otherwise usual
     * business fields (stage, salesperson...), then any relational or selection field.
     */
    getDefaultGroupBy(info, excludedName = false) {
        const fields = this.getGroupByFields().filter((field) => field.name !== excludedName);
        const byName = Object.fromEntries(fields.map((field) => [field.name, field]));
        const preferred = info.dateFirst
            ? [...PREFERRED_DATE_GROUP_BYS, ...PREFERRED_GROUP_BYS]
            : [...PREFERRED_GROUP_BYS, ...PREFERRED_DATE_GROUP_BYS];
        const field =
            preferred.map((name) => byName[name]).find(Boolean) ||
            fields.find((field) => ["many2one", "selection"].includes(field.type)) ||
            fields.find((field) => field.name !== "active") ||
            fields[0];
        return field?.name || false;
    }

    getListableFields() {
        return this.state.fields.filter((field) => !UNLISTABLE_TYPES.includes(field.type));
    }

    getOrderFields() {
        return this.state.fields.filter((field) => field.store && field.sortable !== false);
    }

    getFieldLabel(fieldName) {
        return this.state.fields.find((field) => field.name === fieldName)?.string || fieldName;
    }

    isTemporal(fieldName) {
        const field = this.state.fields.find((field) => field.name === fieldName);
        return Boolean(field && TEMPORAL_TYPES.includes(field.type));
    }

    getOrderTitle() {
        return this.props.block.order_desc ? _t("Descending") : _t("Ascending");
    }

    hasFilter() {
        return (this.props.block.domain || "[]").replace(/\s/g, "") !== "[]";
    }

    update(changes) {
        this.props.onUpdate(changes);
    }

    async onModelSelected({ technical, label }) {
        if (technical === this.props.block.model) {
            return;
        }
        await this.loadFields(technical);
        const changes = {
            model: technical,
            model_label: label,
            domain: "[]",
            measure: false,
            aggregate: "count",
            group_by: false,
            sub_group_by: false,
            list_fields: [],
            order_by: false,
        };
        Object.assign(changes, this.getDefaultOptions(this.getInfo(), changes));
        this.update(changes);
    }

    /**
     * Options preselected so that a block shows something as soon as its model is
     * chosen, or its type is changed.
     */
    getDefaultOptions(info, block) {
        const changes = {};
        if (info.kind === "grouped" && !block.group_by) {
            changes.group_by = this.getDefaultGroupBy(info);
        }
        if (info.subGroupBy === "required" && !block.sub_group_by) {
            changes.sub_group_by = this.getDefaultGroupBy({}, changes.group_by || block.group_by);
        }
        if (info.kind === "records" && !block.list_fields?.length) {
            const preferred = ["name", "date", "date_order", "partner_id", "user_id", "amount_total", "state"];
            const fieldNames = this.getListableFields().map((field) => field.name);
            changes.list_fields = preferred.filter((name) => fieldNames.includes(name)).slice(0, 4);
            changes.order_by = fieldNames.includes("create_date") ? "create_date" : false;
        }
        return changes;
    }

    onBlockTypeChange(ev) {
        const blockType = ev.target.value;
        const changes = { block_type: blockType };
        if (this.props.block.model) {
            Object.assign(changes, this.getDefaultOptions(BLOCK_TYPES_BY_NAME[blockType], this.props.block));
        }
        this.update(changes);
    }

    onAggregateChange(ev) {
        const aggregate = ev.target.value;
        const changes = { aggregate };
        if (aggregate !== "count" && !this.props.block.measure) {
            changes.measure = this.getMeasureFields()[0]?.name || false;
        }
        if (aggregate === "count") {
            changes.measure = false;
        }
        this.update(changes);
    }

    onSelectChange(key, ev) {
        this.update({ [key]: ev.target.value || false });
    }

    onNumberChange(key, ev) {
        const value = parseFloat(ev.target.value);
        this.update({ [key]: Number.isNaN(value) ? 0 : value });
    }

    onNameInput(ev) {
        this.update({ name: ev.target.value, customName: Boolean(ev.target.value) });
    }

    onTextInput(ev) {
        this.update({ text_content: ev.target.value });
    }

    addListField(ev) {
        const fieldName = ev.target.value;
        ev.target.value = "";
        if (fieldName && !this.props.block.list_fields.includes(fieldName)) {
            this.update({ list_fields: [...this.props.block.list_fields, fieldName] });
        }
    }

    removeListField(fieldName) {
        this.update({ list_fields: this.props.block.list_fields.filter((name) => name !== fieldName) });
    }

    editFilter() {
        this.dialogService.add(DomainSelectorDialog, {
            title: _t("Filter the records"),
            resModel: this.props.block.model,
            domain: this.props.block.domain || "[]",
            isDebugMode: Boolean(this.env.debug),
            onConfirm: (domain) => this.update({ domain }),
        });
    }

    clearFilter() {
        this.update({ domain: "[]" });
    }
}
