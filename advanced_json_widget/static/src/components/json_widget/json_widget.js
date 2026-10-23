import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, proxy, signal, useExternalListener, onWillUpdateProps, useEffect } from "@odoo/owl";
import { TagsList } from "@web/core/tags_list/tags_list";
import { _t } from "@web/core/l10n/translation";

const TAG_COLOR_COUNT = 5;

/**
 * JSON Widget Component
 */
export class JsonWidget extends Component {
    static template = "advanced_json_widget.JsonWidget";
    static components = { TagsList };
    static props = { ...standardFieldProps };

    /**
     * Component initialization
     */
    setup() {
        this.notification = useService("notification");
        this.state = proxy({
            showDropdown: false,
            entries: [],
            dropdownReady: false,
        });
        this.jsonDropdown = signal.ref();
        this.addLineButton = signal.ref();
        this.jsonWidget = signal.ref();

        this.onWindowClickListener = (ev) => {
            if (
                this.state.showDropdown &&
                this.jsonDropdown.el &&
                !this.jsonDropdown.el.contains(ev.target) &&
                !this.jsonWidget.el?.contains(ev.target) &&
                !ev.target.isSameNode(document.documentElement)
            ) {
                this.closeJsonEditor();
            }
        };
        useExternalListener(window, "click", this.onWindowClickListener, true);
        this.initializeEntries();

        onWillUpdateProps((nextProps) => {
            if (!this.state.showDropdown && nextProps.record?.data?.[this.props.name] !== this.props.record?.data?.[this.props.name]) {
                this.initializeEntries(nextProps.record?.data?.[this.props.name], true);
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
     * Initialize entries from JSON data or JSON string.
     * @param {Object|string} tableData - Optional JSON data.
     * @param {boolean} updateProps - Use provided data instead of current record.
     */
    initializeEntries(tableData, updateProps = false) {
        const rawData = updateProps ? tableData : this.props.record?.data?.[this.props.name];
        this.state.entries = this.formatJsonToEntries(rawData);
    }

    /**
     * Convert JSON object or string to array of key-value entries.
     */
    formatJsonToEntries(jsonData) {
        let data = jsonData;
        if (typeof data === "string") {
            try {
                data = JSON.parse(data);
            } catch {
                data = {};
            }
        }
        if (typeof data !== "object" || data === null) {
            data = {};
        }
        return Object.entries(data).map(([key, value], index) => ({
            id: `line_${index}_${Date.now()}`,
            key: String(key),
            value: typeof value === "object" && value !== null ? JSON.stringify(value) : String(value ?? ""),
        }));
    }

    /**
     * Convert entries array back to JSON object.
     */
    formatEntriesToJson() {
        return this.state.entries
            .filter((entry) => entry.key && entry.key.trim())
            .reduce((acc, entry) => {
                let value = entry.value ? entry.value.trim() : "";
                if (value === "false" || value === "true" || value === "null") {
                    if (value === "true") value = true;
                    else if (value === "false") value = false;
                    else if (value === "null") value = null;
                } else if (/^-?\d+$/.test(value)) {
                    value = Number(value); // Integers
                } else if (/^-?\d+\.\d+$/.test(value)) {
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
     * Update the record field with JSON data (or JSON string for Char/Text fields).
     */
    async updateRecord() {
        const jsonData = this.formatEntriesToJson();
        const fieldType = this.props.record?.fields?.[this.props.name]?.type;
        const val = (fieldType === "char" || fieldType === "text") ? JSON.stringify(jsonData) : jsonData;
        await this.props.record.update({ [this.props.name]: val });
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
            this.state.dropdownReady = false;
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
        const newId = `line_${this.state.entries.length}_${Date.now()}`;
        this.state.entries.push({ id: newId, key: "", value: "" });
        setTimeout(() => {
            const textInputs = this.jsonDropdown.el?.querySelectorAll('input[type="text"]') || [];
            if (textInputs.length >= 2) {
                textInputs[textInputs.length - 2]?.focus();
            }
        }, 50);
    }

    /**
     * Delete a line by entry object or index.
     */
    async deleteLine(entry) {
        const index = typeof entry === "number" ? entry : this.state.entries.indexOf(entry);
        if (index !== -1) {
            this.state.entries.splice(index, 1);
        }
        await this.updateRecord();
    }

    onKeyInput(ev, entry) {
        entry.key = ev.target.value;
    }

    onValueInput(ev, entry) {
        entry.value = ev.target.value;
    }

    /**
     * Tags to display summary of JSON.
     */
    jsonSummaryTags() {
        const jsonData = this.formatEntriesToJson();
        return Object.keys(jsonData).map((key, index) => ({
            id: `tag_${key}_${index}`,
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
    supportedTypes: ["json", "char", "text"],
};

registry.category("fields").add("json_widget", jsonField);