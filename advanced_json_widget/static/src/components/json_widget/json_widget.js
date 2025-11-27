/** @odoo-module **/
/**
 * JSON widget: custom field widget to edit JSON fields as key/value pairs.
 */
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, useExternalListener, onWillUpdateProps, useEffect } from "@odoo/owl";
import { TagsList } from "@web/core/tags_list/tags_list";
import { _t } from "@web/core/l10n/translation";

const TAG_COLOR_COUNT = 5;
/**
 * JSON Widget Component
 */
export class JsonWidget extends Component {
    static template = "web.JsonWidget";
    static components = { TagsList };
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

        onWillUpdateProps((nextProps) => {
            if (nextProps.data[this.props.name] !== this.props.data[this.props.name]) {
                this.initializeEntries(nextProps.data[this.props.name], true);
            }
        });

        // Focus only when dropdown is opened
        useEffect(() => {
            if (this.state.showDropdown && !this.state.dropdownReady) {
                this.state.dropdownReady = true;
                this.onDropdownMounted();
            }
        }, () => [this.state.showDropdown]);
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
            .filter((entry) => entry.key.trim())
            .reduce((acc, entry) => {
                let value = entry.value.trim();
                if (value === "" || value === "false" || value === "true" || value === "null") {
                    // Handle primitives
                    if (value === "true") value = true;
                    else if (value === "false") value = false;
                    else if (value === "null") value = null;
                    else value = entry.value; // Keep empty as-is
                } else if (/^\d+$/.test(value)) {
                    value = Number(value); // Integers
                } else if (/^\d+\.\d+$/.test(value)) {
                    value = parseFloat(value); // Floats
                } else {
                    try {
                        value = JSON.parse(value); // Objects/arrays
                    } catch {
                        // Keep as string
                    }
                }
                acc[entry.key.trim()] = value;
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
        // Sync state.entries with saved JSON
        this.initializeEntries();
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
            this.state.dropdownReady = false; // Reset to allow focus on open
            await Promise.resolve();
        }
    }
    /**
     * Close the JSON editor and update record.
     */
    async closeJsonEditor() {
        await this.updateRecord();
        this.state.showDropdown = false;
        this.state.dropdownReady = false;
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
    validateEntry(entry, isNewKey = false) {
        const keys = this.state.entries
            .filter((e) => e.id !== entry.id) // Exclude current entry for comparison
            .map((e) => e.key.trim())
            .filter(Boolean);
        const isDuplicate = keys.includes(entry.key.trim());

        if (!entry.key.trim()) {
            this.state.hasEmptyKey = true;
            this.notification.add(_t("Key cannot be empty"), { type: "warning" });
            return false;
        }
        if (isDuplicate && isNewKey) {
            this.state.hasDuplicateKey = true;
            this.notification.add(_t("Duplicate keys are not allowed"), { type: "warning" });
            return false;
        }
        this.state.hasEmptyKey = false;
        this.state.hasDuplicateKey = false;
        return true;
    }
    onKeyInput(ev, entry) {
        const newKey = ev.target.value;
        // Only update if the key is valid (not a duplicate)
        if (this.validateEntry({ ...entry, key: newKey }, true)) {
            entry.key = newKey;
            this.validateAndUpdate(entry);
        } else {
            ev.target.value = entry.key; // Revert to previous value
        }
    }

    onValueInput(ev, entry) {
        entry.value = ev.target.value;
        this.validateAndUpdate(entry);
    }

    async validateAndUpdate(entry) {
        if (this.validateEntry(entry)) {
            await this.updateRecord();
        }
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
    }
    /**
     * Focus first input when dropdown mounted.
     */
    onDropdownMounted() {
        const firstInput = this.jsonDropdown.el?.querySelector('input[type="text"]');
        firstInput?.focus();
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
        readonly: !!attrs.readonly,
    }),
};
registry.category("fields").add("json_widget", jsonField);