/** @odoo-module **/
/**
 * JSON widget: custom field widget to edit JSON fields as key/value pairs.
 */
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, useExternalListener, onWillUpdateProps } from "@odoo/owl";
import { Field } from "@web/views/fields/field";
import { Record } from "@web/model/record";
import { TagsList } from "@web/core/tags_list/tags_list";
import { _t } from "@web/core/l10n/translation";
import { useRecordObserver } from "@web/model/relational_model/utils";

const TAG_COLOR_COUNT = 5;
/**
 * JSON Widget Component
 */
export class JsonWidget extends Component {
    static template = "web.JsonWidget";
    static components = { TagsList, Record, Field };
    static props = { ...standardFieldProps };
    /**
     * Component initialization
     */
    setup() {
        this.notification = useService("notification");
        this.state = useState({
            showDropdown: false,
            entries: [],
            dropdownReady: false,
            isLastEntryValid: true,
            hasEmptyKey: false,
            hasDuplicateKey: false,
        });
        this.jsonDropdown = useRef("jsonDropdown");
        this.onWindowClickListener = (ev) => {
            if (
                this.state.showDropdown &&
                this.jsonDropdown.el &&
                !this.jsonDropdown.el.contains(ev.target) &&
                !ev.target.isSameNode(document.documentElement)
            ) {
                this.closeJsonEditor();
            }
        };
        useExternalListener(window, "click", this.onWindowClickListener, true);
        this.initializeEntries();

        useRecordObserver((nextProps) => {
            this.initializeEntries(nextProps.data[this.props.name], true);
        });
        this.initializeEntries();  // Initial call
        onWillUpdateProps((nextProps) => {
        if (nextProps.data[this.props.name] !== this.props.data[this.props.name]) {
            this.initializeEntries(nextProps.data[this.props.name], true);
        }
    });
    }
    /**
     * Initialize entries from JSON data.
     * @param {Object} tableData - Optional JSON data.
     * @param {boolean} updateProps - Use provided data instead of current record.
     */
    initializeEntries(tableData, updateProps = false) {
        const jsonData = updateProps ? tableData || {} : this.props.record.data[this.props.name];
        this.state.entries = this.formatJsonToEntries(jsonData);
    }
    /**
     * Convert JSON object to array of key-value entries.
     */
    formatJsonToEntries(jsonData) {
        return Object.entries(jsonData || {}).map(([key, value], index) => ({
            index,
            id: `line_${index}`,
            key,
            value: typeof value === "object" ? JSON.stringify(value) : String(value),
        }));
    }
    /**
     * Convert entries array back to JSON object.
     */
    formatEntriesToJson() {
        return this.state.entries
            .filter((entry) => entry.key)
            .reduce((acc, entry) => {
                try {
                    const value = entry.value.startsWith("{") || entry.value.startsWith("[")
                        ? JSON.parse(entry.value)
                        : entry.value;
                    acc[entry.key.trim()] = value;
                } catch {
                    acc[entry.key.trim()] = entry.value;
                }
                return acc;
            }, {});
    }
    /**
     * Update the record field with JSON data.
     */
    async updateRecord() {
        const jsonData = this.formatEntriesToJson();
        await this.props.record.update({ [this.props.name]: jsonData });
        this.state.isLastEntryValid = true;
        this.state.hasDuplicateKey = false;
        this.state.hasEmptyKey = false;
    }
    /**
     * Handle Escape key to close editor.
     */
    onWidgetKeydown(ev) {
        if (ev.key === "Escape") {
            this.closeJsonEditor();
        }
    }
    /**
     * Open the JSON editor dropdown.
     */
    async openJsonEditor() {
        if (!this.props.readonly) {
            this.state.showDropdown = true;
            await Promise.resolve();
            this.state.dropdownReady = true;
        }
    }
    /**
     * Close the JSON editor and update record.
     */
    async closeJsonEditor() {
        await this.updateRecord();
        this.state.showDropdown = false;
    }
    /**
     * Add a new empty line.
     */
    addLine() {
        const lastEntry = this.state.entries[this.state.entries.length - 1];
        this.state.isLastEntryValid = this.state.entries.length === 0 || !!lastEntry?.key;

        if (this.state.isLastEntryValid) {
            const newId = `line_${this.state.entries.length}`;
            this.state.entries.push({ id: newId, key: "", value: "" });
        } else {
            const textInputs = this.jsonDropdown.el?.querySelectorAll('input[type="text"]') || [];
            if (this.state.hasDuplicateKey) {
                this.notification.add(_t("Duplicate keys are not allowed"), { type: "warning" });
            } else if (this.state.hasEmptyKey) {
                this.notification.add(_t("Key cannot be empty"), { type: "warning" });
            } else {
                this.notification.add(_t("Empty entry not allowed"), { type: "warning" });
            }
            textInputs[textInputs.length - 2]?.focus();
        }
    }
    /**
     * Delete a line by index.
     */
    async deleteLine(index) {
        if (typeof index === "number") {
            this.state.entries.splice(index, 1);
        } else {
            this.state.entries.pop();
        }
        await this.updateRecord();
    }
    /**
     * Validate entry: no empty key and no duplicates.
     */
    validateEntry(entry) {
        const keys = this.state.entries.map((e) => e.key);
        const isDuplicate = keys.filter((k) => k === entry.key).length > 1;

        if (entry.key && entry.value) {
            if (isDuplicate) {
                this.state.hasDuplicateKey = true;
                this.notification.add(_t("Duplicate keys are not allowed"), { type: "warning" });
                return false;
            }
            this.state.hasDuplicateKey = false;
            this.state.hasEmptyKey = false;
            return true;
        } else if (entry.value && !entry.key) {
            this.state.hasEmptyKey = true;
            this.notification.add(_t("Key cannot be empty"), { type: "warning" });
            return false;
        }
        return true;
    }
    /**
     * Update a specific entry.
     */
    async updateEntry(record, changes, entry) {
        const idx = this.state.entries.findIndex((e) => e.id === entry.id);
        if (idx !== -1) {
            this.state.entries[idx] = { ...this.state.entries[idx], ...changes };
            if (this.state.entries[idx].key && this.state.entries[idx].value) {
                await this.updateRecord();
            }
        }
    }
    /**
     * Create props for Record component.
     */
    recordProps(entry) {
        const fields = {
            key: { string: _t("Key"), type: "char" },
            value: { string: _t("Value"), type: "char" },
        };
        return {
            fields,
            values: { key: entry.key || "", value: entry.value === "false" ? "" : entry.value },
            activeFields: fields,
            onRecordChanged: async (record, changes) => {
                if (this.validateEntry({ ...entry, ...changes })) {
                    await this.updateEntry(record, changes, entry);
                }
            },
        };
    }
    /**
     * Tags to display summary of JSON.
     */
    jsonSummaryTags() {
        const jsonData = this.props.record.data[this.props.name] || {};
        return Object.keys(jsonData).map((key, index) => ({
            id: `tag_${index + 1}`,
            text: key,
            colorIndex: (index % TAG_COLOR_COUNT) + 1,
            onClick: (ev) => this.handleTagClick(ev),
        }));
    }
    /**
     * Handle tag click to open editor.
     */
    async handleTagClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        await this.openJsonEditor();
        await Promise.resolve();

        const firstInput = this.jsonDropdown.el?.querySelector('input[type="text"]');
        firstInput?.focus();
    }
    /**
     * Focus first input when dropdown mounted.
     */
    onDropdownMounted() {
        if (this.state.dropdownReady) {
            const firstInput = this.jsonDropdown.el?.querySelector('input[type="text"]');
            firstInput?.focus();
        }
    }
}
/**
 * Field definition for JsonWidget.
 */
export const jsonField = {
    component: JsonWidget,
    displayName: _t("JSON Editor"),
    supportedTypes: ["json"],
    extractProps: ({ attrs }) => ({
        readonly: attrs.readonly === "true",
    }),
};

registry.category("fields").add("json_widget", jsonField);